from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import LeagueCreate, LeagueUpdate, LeagueResponse
from db.models import League

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("", response_model=list[LeagueResponse])
def get_leagues():
    with Session(engine) as session:
        return session.execute(select(League)).scalars().all()


@router.get("/{league_id}", response_model=LeagueResponse)
def get_league(league_id: int):
    with Session(engine) as session:
        league = session.get(League, league_id)
        if league is None:
            raise HTTPException(status_code=404, detail="League not found")
        return league


@router.post("", response_model=LeagueResponse, status_code=201)
def create_league(data: LeagueCreate):
    with Session(engine) as session:
        league = League(**data.model_dump())
        session.add(league)
        session.commit()
        session.refresh(league)
        return league


@router.patch("/{league_id}", response_model=LeagueResponse)
def update_league(league_id: int, data: LeagueUpdate):
    with Session(engine) as session:
        league = session.get(League, league_id)
        if league is None:
            raise HTTPException(status_code=404, detail="League not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(league, key, value)
        session.commit()
        session.refresh(league)
        return league


@router.delete("/{league_id}", status_code=204)
def delete_league(league_id: int):
    with Session(engine) as session:
        league = session.get(League, league_id)
        if league is None:
            raise HTTPException(status_code=404, detail="League not found")
        session.delete(league)
        session.commit()