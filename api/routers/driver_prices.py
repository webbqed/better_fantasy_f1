from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import DriverPriceCreate, DriverPriceUpdate, DriverPriceResponse
from db.models import DriverPrice

router = APIRouter(prefix="/driver-prices", tags=["Driver Prices"])


@router.get("", response_model=list[DriverPriceResponse])
def get_driver_prices():
    with Session(engine) as session:
        return session.execute(select(DriverPrice)).scalars().all()


@router.get("/{price_id}", response_model=DriverPriceResponse)
def get_driver_price(price_id: int):
    with Session(engine) as session:
        price = session.get(DriverPrice, price_id)
        if price is None:
            raise HTTPException(status_code=404, detail="Driver price not found")
        return price


@router.post("", response_model=DriverPriceResponse, status_code=201)
def create_driver_price(data: DriverPriceCreate):
    with Session(engine) as session:
        price = DriverPrice(**data.model_dump())
        session.add(price)
        session.commit()
        session.refresh(price)
        return price


@router.patch("/{price_id}", response_model=DriverPriceResponse)
def update_driver_price(price_id: int, data: DriverPriceUpdate):
    with Session(engine) as session:
        price = session.get(DriverPrice, price_id)
        if price is None:
            raise HTTPException(status_code=404, detail="Driver price not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(price, key, value)
        session.commit()
        session.refresh(price)
        return price


@router.delete("/{price_id}", status_code=204)
def delete_driver_price(price_id: int):
    with Session(engine) as session:
        price = session.get(DriverPrice, price_id)
        if price is None:
            raise HTTPException(status_code=404, detail="Driver price not found")
        session.delete(price)
        session.commit()