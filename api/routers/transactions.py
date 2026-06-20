from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import TransactionCreate, TransactionResponse
from db.models import Transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionResponse])
def get_transactions():
    with Session(engine) as session:
        return session.execute(select(Transaction)).scalars().all()


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int):
    with Session(engine) as session:
        transaction = session.get(Transaction, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate):
    with Session(engine) as session:
        transaction = Transaction(**data.model_dump())
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        return transaction


# Note: no update/delete here — transactions are a historical record and are
# normally immutable once created. Add them later if your design needs them.