from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db
from ..services.parser import parse_link
from ..services.checker import run_single_check

router = APIRouter()


def build_server_list_item(db: Session, server: models.Server) -> schemas.ServerListItem:
    last_check = (
        db.query(models.Check)
        .filter(models.Check.server_id == server.id)
        .order_by(models.Check.checked_at.desc())
        .first()
    )

    return schemas.ServerListItem(
        id=server.id,
        name=server.name,
        type=server.type,
        host=server.host,
        port=server.port,
        enabled=server.enabled,
        group_id=server.group_id,
        group=server.group,
        raw_link=server.raw_link,
        last_status=last_check.status if last_check else None,
        last_latency_ms=last_check.latency_ms if last_check else None,
        last_checked_at=last_check.checked_at if last_check else None,
    )



@router.post("/", response_model=schemas.ServerListItem)
def create_server(payload: schemas.ServerCreate, db: Session = Depends(get_db)):
    try:
        parsed = parse_link(payload.link)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    name = (payload.name or parsed.name or "unnamed").strip()

    server = models.Server(**parsed.to_server_kwargs())
    server.name = name

    db.add(server)
    db.commit()
    db.refresh(server)

    return build_server_list_item(db, server)


@router.get("/", response_model=List[schemas.ServerListItem])
def list_servers(db: Session = Depends(get_db)):
    servers = db.query(models.Server).order_by(models.Server.id).all()
    return [build_server_list_item(db, s) for s in servers]


@router.get("/{server_id}", response_model=schemas.ServerDetail)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
    return {"ok": True}


@router.post("/{server_id}/toggle", response_model=schemas.ServerListItem)
def toggle_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    server.enabled = not server.enabled
    db.commit()
    db.refresh(server)
    return build_server_list_item(db, server)


@router.post("/{server_id}/test", response_model=schemas.ServerListItem)
def test_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    run_single_check(db, server)
    db.refresh(server)
    return build_server_list_item(db, server)


@router.put("/{server_id}", response_model=schemas.ServerListItem)
def update_server(
    server_id: int,
    payload: schemas.ServerUpdate,
    db: Session = Depends(get_db),
):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    data = payload.dict(exclude_unset=True)


    link = data.pop("link", None)
    if link:
        try:
            parsed = parse_link(link)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        parsed_kwargs = parsed.to_server_kwargs()
        for k, v in parsed_kwargs.items():
            setattr(server, k, v)
        server.raw_link = link

    for k, v in data.items():
        setattr(server, k, v)

    db.commit()
    db.refresh(server)
    return build_server_list_item(db, server)
