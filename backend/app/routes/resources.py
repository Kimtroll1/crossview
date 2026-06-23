from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.recommendation import Recommendation
from app.models.resource_click import ResourceClick
from app.models.user import User
from app.security.tokens import get_current_user

router = APIRouter(prefix="/api/resources", tags=["resources"])


@router.post("/{resource_id}/click")
def record_click(
    resource_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resource = db.query(Recommendation).filter(Recommendation.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="추천 자료를 찾을 수 없습니다.")
    db.add(ResourceClick(user_id=user.id, recommendation_id=resource.id, category=resource.category))
    db.commit()
    return {"ok": True, "resourceId": resource_id}
