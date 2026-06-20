from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import DriverCreate, DriverUpdate, DriverResponse
from db.models import Driver

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
def get_drivers():
    with Session(engine) as session:
        return session.execute(select(Driver)).scalars().all()


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int):
    with Session(engine) as session:
        driver = session.get(Driver, driver_id)
        if driver is None:
            raise HTTPException(status_code=404, detail="Driver not found")
        return driver


@router.post("", response_model=DriverResponse, status_code=201)
def create_driver(data: DriverCreate):
    with Session(engine) as session:
        driver = Driver(**data.model_dump())
        session.add(driver)
        session.commit()
        session.refresh(driver)
        return driver


@router.patch("/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: int, data: DriverUpdate):
    with Session(engine) as session:
        driver = session.get(Driver, driver_id)
        if driver is None:
            raise HTTPException(status_code=404, detail="Driver not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(driver, key, value)
        session.commit()
        session.refresh(driver)
        return driver


@router.delete("/{driver_id}", status_code=204)
def delete_driver(driver_id: int):
    with Session(engine) as session:
        driver = session.get(Driver, driver_id)
        if driver is None:
            raise HTTPException(status_code=404, detail="Driver not found")
        session.delete(driver)
        session.commit()