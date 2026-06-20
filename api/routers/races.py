from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import RaceCreate, RaceUpdate, RaceResponse
from db.models import Race

router = APIRouter(prefix="/races", tags=["Races"])


@router.get("", response_model=list[RaceResponse])
def get_races():
    with Session(engine) as session:
        return session.execute(select(Race)).scalars().all()


@router.get("/{race_id}", response_model=RaceResponse)
def get_race(race_id: int):
    with Session(engine) as session:
        race = session.get(Race, race_id)
        if race is None:
            raise HTTPException(status_code=404, detail="Race not found")
        return race


@router.post("", response_model=RaceResponse, status_code=201)
def create_race(data: RaceCreate):
    with Session(engine) as session:
        race = Race(**data.model_dump())
        session.add(race)
        session.commit()
        session.refresh(race)
        return race


@router.patch("/{race_id}", response_model=RaceResponse)
def update_race(race_id: int, data: RaceUpdate):
    with Session(engine) as session:
        race = session.get(Race, race_id)
        if race is None:
            raise HTTPException(status_code=404, detail="Race not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(race, key, value)
        session.commit()
        session.refresh(race)
        return race


@router.delete("/{race_id}", status_code=204)
def delete_race(race_id: int):
    with Session(engine) as session:
        race = session.get(Race, race_id)
        if race is None:
            raise HTTPException(status_code=404, detail="Race not found")
        session.delete(race)
        session.commit()