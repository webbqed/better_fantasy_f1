from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import MatchupCreate, MatchupUpdate, MatchupResponse
from db.models import Matchup

router = APIRouter(prefix="/matchups", tags=["Matchups"])


@router.get("", response_model=list[MatchupResponse])
def get_matchups():
    with Session(engine) as session:
        return session.execute(select(Matchup)).scalars().all()


@router.get("/{matchup_id}", response_model=MatchupResponse)
def get_matchup(matchup_id: int):
    with Session(engine) as session:
        matchup = session.get(Matchup, matchup_id)
        if matchup is None:
            raise HTTPException(status_code=404, detail="Matchup not found")
        return matchup


@router.post("", response_model=MatchupResponse, status_code=201)
def create_matchup(data: MatchupCreate):
    with Session(engine) as session:
        matchup = Matchup(**data.model_dump())
        session.add(matchup)
        session.commit()
        session.refresh(matchup)
        return matchup


@router.patch("/{matchup_id}", response_model=MatchupResponse)
def update_matchup(matchup_id: int, data: MatchupUpdate):
    with Session(engine) as session:
        matchup = session.get(Matchup, matchup_id)
        if matchup is None:
            raise HTTPException(status_code=404, detail="Matchup not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(matchup, key, value)
        session.commit()
        session.refresh(matchup)
        return matchup


@router.delete("/{matchup_id}", status_code=204)
def delete_matchup(matchup_id: int):
    with Session(engine) as session:
        matchup = session.get(Matchup, matchup_id)
        if matchup is None:
            raise HTTPException(status_code=404, detail="Matchup not found")
        session.delete(matchup)
        session.commit()