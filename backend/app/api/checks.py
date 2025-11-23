from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db

router = APIRouter()


@router.get("/{server_id}", response_model=List[schemas.CheckRead])
def get_checks(
    server_id: int,
    minutes: int = Query(60, ge=1, le=10080),  # تا ۷ روز
    db: Session = Depends(get_db),
):
    server = db.query(models.Server).filter(models.Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    since = datetime.utcnow() - timedelta(minutes=minutes)
    checks = (
        db.query(models.Check)
        .filter(
            models.Check.server_id == server_id,
            models.Check.checked_at >= since,
        )
        .order_by(models.Check.checked_at.asc())
        .all()
    )
    return checks
