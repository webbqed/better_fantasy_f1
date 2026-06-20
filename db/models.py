import os
from sqlalchemy import create_engine, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    commissioner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    season_year: Mapped[int] = mapped_column()
    starting_bankroll: Mapped[float] = mapped_column()
    weekly_win_bonus: Mapped[float] = mapped_column()
    min_drivers: Mapped[int] = mapped_column()
    max_drivers: Mapped[int] = mapped_column()
    min_spend_per_driver: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class LeagueMember(Base):
    __tablename__ = "league_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cash_balance: Mapped[float] = mapped_column()
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_number: Mapped[int] = mapped_column(unique=True)
    full_name: Mapped[str] = mapped_column()
    team_name: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)


class Race(Base):
    __tablename__ = "races"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_year: Mapped[int] = mapped_column()
    round_number: Mapped[int] = mapped_column()
    race_name: Mapped[str] = mapped_column()
    race_date: Mapped[datetime] = mapped_column()
    is_completed: Mapped[bool] = mapped_column(default=False)


class DriverPrice(Base):
    __tablename__ = "driver_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    price: Mapped[float] = mapped_column()
    win_prob: Mapped[float] = mapped_column()
    top3_prob: Mapped[float] = mapped_column()
    dnf_prob: Mapped[float] = mapped_column()
    avg_pts: Mapped[float] = mapped_column()
    std_per_100: Mapped[float] = mapped_column()
    median_position: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_member_id: Mapped[int] = mapped_column(ForeignKey("league_members.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    shares: Mapped[float] = mapped_column()
    avg_purchase_price: Mapped[float] = mapped_column()


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_member_id: Mapped[int] = mapped_column(ForeignKey("league_members.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    type: Mapped[str] = mapped_column()
    shares: Mapped[float] = mapped_column()
    price_per_share: Mapped[float] = mapped_column()
    total_value: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class RaceResult(Base):
    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    finish_position: Mapped[int] = mapped_column()
    fantasy_points: Mapped[float] = mapped_column()


class Matchup(Base):
    __tablename__ = "matchups"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"))
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"))
    home_member_id: Mapped[int] = mapped_column(ForeignKey("league_members.id"))
    away_member_id: Mapped[int] = mapped_column(ForeignKey("league_members.id"))
    home_points: Mapped[float | None] = mapped_column(nullable=True)
    away_points: Mapped[float | None] = mapped_column(nullable=True)
    winner_member_id: Mapped[int | None] = mapped_column(ForeignKey("league_members.id"), nullable=True)
    type: Mapped[str] = mapped_column()
    knockout_round: Mapped[int | None] = mapped_column(nullable=True)


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created successfully")
