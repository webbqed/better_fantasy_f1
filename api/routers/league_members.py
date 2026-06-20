from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import LeagueMemberCreate, LeagueMemberUpdate, LeagueMemberResponse
from db.models import LeagueMember

router = APIRouter(prefix="/league-members", tags=["League Members"])


@router.get("", response_model=list[LeagueMemberResponse])
def get_league_members():
    with Session(engine) as session:
        return session.execute(select(LeagueMember)).scalars().all()


@router.get("/{member_id}", response_model=LeagueMemberResponse)
def get_league_member(member_id: int):
    with Session(engine) as session:
        member = session.get(LeagueMember, member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="League member not found")
        return member


@router.post("", response_model=LeagueMemberResponse, status_code=201)
def create_league_member(data: LeagueMemberCreate):
    with Session(engine) as session:
        member = LeagueMember(**data.model_dump())
        session.add(member)
        session.commit()
        session.refresh(member)
        return member


@router.patch("/{member_id}", response_model=LeagueMemberResponse)
def update_league_member(member_id: int, data: LeagueMemberUpdate):
    with Session(engine) as session:
        member = session.get(LeagueMember, member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="League member not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(member, key, value)
        session.commit()
        session.refresh(member)
        return member


@router.delete("/{member_id}", status_code=204)
def delete_league_member(member_id: int):
    with Session(engine) as session:
        member = session.get(LeagueMember, member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="League member not found")
        session.delete(member)
        session.commit()