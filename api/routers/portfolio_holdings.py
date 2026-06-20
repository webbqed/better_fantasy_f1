from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import (
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
    PortfolioHoldingResponse,
)
from db.models import PortfolioHolding

router = APIRouter(prefix="/portfolio-holdings", tags=["Portfolio Holdings"])


@router.get("", response_model=list[PortfolioHoldingResponse])
def get_portfolio_holdings():
    with Session(engine) as session:
        return session.execute(select(PortfolioHolding)).scalars().all()


@router.get("/{holding_id}", response_model=PortfolioHoldingResponse)
def get_portfolio_holding(holding_id: int):
    with Session(engine) as session:
        holding = session.get(PortfolioHolding, holding_id)
        if holding is None:
            raise HTTPException(status_code=404, detail="Portfolio holding not found")
        return holding


@router.post("", response_model=PortfolioHoldingResponse, status_code=201)
def create_portfolio_holding(data: PortfolioHoldingCreate):
    with Session(engine) as session:
        holding = PortfolioHolding(**data.model_dump())
        session.add(holding)
        session.commit()
        session.refresh(holding)
        return holding


@router.patch("/{holding_id}", response_model=PortfolioHoldingResponse)
def update_portfolio_holding(holding_id: int, data: PortfolioHoldingUpdate):
    with Session(engine) as session:
        holding = session.get(PortfolioHolding, holding_id)
        if holding is None:
            raise HTTPException(status_code=404, detail="Portfolio holding not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(holding, key, value)
        session.commit()
        session.refresh(holding)
        return holding


@router.delete("/{holding_id}", status_code=204)
def delete_portfolio_holding(holding_id: int):
    with Session(engine) as session:
        holding = session.get(PortfolioHolding, holding_id)
        if holding is None:
            raise HTTPException(status_code=404, detail="Portfolio holding not found")
        session.delete(holding)
        session.commit()