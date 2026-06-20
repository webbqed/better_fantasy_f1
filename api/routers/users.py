from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import engine
from api.schemas import UserCreate, UserUpdate, UserResponse
from db.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def get_users():
    with Session(engine) as session:
        return session.execute(select(User)).scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user


@router.post("", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate):
    with Session(engine) as session:
        # TODO: This stores the password as-is. Before going live, hash it with
        # something like passlib/bcrypt and store the hash instead of plaintext.
        user = User(
            username=data.username,
            email=data.email,
            password_hash=data.password,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        session.commit()
        session.refresh(user)
        return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()