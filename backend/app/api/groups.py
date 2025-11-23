from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.ServerGroupOut])
def list_groups(db: Session = Depends(get_db)):
    return (
        db.query(models.ServerGroup)
        .order_by(models.ServerGroup.sort_order, models.ServerGroup.name)
        .all()
    )


@router.post("/", response_model=schemas.ServerGroupOut)
def create_group(
    payload: schemas.ServerGroupCreate,
    db: Session = Depends(get_db),
):
    group = models.ServerGroup(**payload.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.put("/{group_id}", response_model=schemas.ServerGroupOut)
def update_group(
    group_id: int,
    payload: schemas.ServerGroupUpdate,
    db: Session = Depends(get_db),
):
    group = db.query(models.ServerGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(group, k, v)

    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(models.ServerGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # سرورهای این گروه را بدون گروه کنیم
    db.query(models.Server).filter(
        models.Server.group_id == group_id
    ).update({models.Server.group_id: None})

    db.delete(group)
    db.commit()
    return {"ok": True}
