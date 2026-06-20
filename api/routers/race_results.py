from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import RaceResultCreate, RaceResultUpdate, RaceResultResponse
from db.models import RaceResult

router = APIRouter(prefix="/race-results", tags=["Race Results"])


@router.get("", response_model=list[RaceResultResponse])
def get_race_results():
    with Session(engine) as session:
        return session.execute(select(RaceResult)).scalars().all()


@router.get("/{result_id}", response_model=RaceResultResponse)
def get_race_result(result_id: int):
    with Session(engine) as session:
        result = session.get(RaceResult, result_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Race result not found")
        return result


@router.post("", response_model=RaceResultResponse, status_code=201)
def create_race_result(data: RaceResultCreate):
    with Session(engine) as session:
        result = RaceResult(**data.model_dump())
        session.add(result)
        session.commit()
        session.refresh(result)
        return result


@router.patch("/{result_id}", response_model=RaceResultResponse)
def update_race_result(result_id: int, data: RaceResultUpdate):
    with Session(engine) as session:
        result = session.get(RaceResult, result_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Race result not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(result, key, value)
        session.commit()
        session.refresh(result)
        return result


@router.delete("/{result_id}", status_code=204)
def delete_race_result(result_id: int):
    with Session(engine) as session:
        result = session.get(RaceResult, result_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Race result not found")
        session.delete(result)
        session.commit()