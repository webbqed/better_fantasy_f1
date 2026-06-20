from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str  # TODO: hash before storing — see note in routers/users.py


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Leagues
# ---------------------------------------------------------------------------
class LeagueCreate(BaseModel):
    name: str
    commissioner_user_id: int
    season_year: int
    starting_bankroll: float
    weekly_win_bonus: float
    min_drivers: int
    max_drivers: int
    min_spend_per_driver: float


class LeagueUpdate(BaseModel):
    name: str | None = None
    commissioner_user_id: int | None = None
    season_year: int | None = None
    starting_bankroll: float | None = None
    weekly_win_bonus: float | None = None
    min_drivers: int | None = None
    max_drivers: int | None = None
    min_spend_per_driver: float | None = None


class LeagueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    commissioner_user_id: int
    season_year: int
    starting_bankroll: float
    weekly_win_bonus: float
    min_drivers: int
    max_drivers: int
    min_spend_per_driver: float
    created_at: datetime


# ---------------------------------------------------------------------------
# League members
# ---------------------------------------------------------------------------
class LeagueMemberCreate(BaseModel):
    league_id: int
    user_id: int
    cash_balance: float


class LeagueMemberUpdate(BaseModel):
    cash_balance: float | None = None


class LeagueMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_id: int
    user_id: int
    cash_balance: float
    joined_at: datetime


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------
class DriverCreate(BaseModel):
    driver_number: int
    full_name: str
    team_name: str
    is_active: bool = True


class DriverUpdate(BaseModel):
    driver_number: int | None = None
    full_name: str | None = None
    team_name: str | None = None
    is_active: bool | None = None


class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_number: int
    full_name: str
    team_name: str
    is_active: bool


# ---------------------------------------------------------------------------
# Races
# ---------------------------------------------------------------------------
class RaceCreate(BaseModel):
    season_year: int
    round_number: int
    race_name: str
    race_date: datetime
    is_completed: bool = False


class RaceUpdate(BaseModel):
    season_year: int | None = None
    round_number: int | None = None
    race_name: str | None = None
    race_date: datetime | None = None
    is_completed: bool | None = None


class RaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season_year: int
    round_number: int
    race_name: str
    race_date: datetime
    is_completed: bool


# ---------------------------------------------------------------------------
# Driver prices
# ---------------------------------------------------------------------------
class DriverPriceCreate(BaseModel):
    driver_id: int
    race_id: int
    price: float
    win_prob: float
    top3_prob: float
    dnf_prob: float
    avg_pts: float
    std_per_100: float
    median_position: float


class DriverPriceUpdate(BaseModel):
    price: float | None = None
    win_prob: float | None = None
    top3_prob: float | None = None
    dnf_prob: float | None = None
    avg_pts: float | None = None
    std_per_100: float | None = None
    median_position: float | None = None


class DriverPriceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    race_id: int
    price: float
    win_prob: float
    top3_prob: float
    dnf_prob: float
    avg_pts: float
    std_per_100: float
    median_position: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Portfolio holdings
# ---------------------------------------------------------------------------
class PortfolioHoldingCreate(BaseModel):
    league_member_id: int
    driver_id: int
    shares: float
    avg_purchase_price: float


class PortfolioHoldingUpdate(BaseModel):
    shares: float | None = None
    avg_purchase_price: float | None = None


class PortfolioHoldingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_member_id: int
    driver_id: int
    shares: float
    avg_purchase_price: float


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------
class TransactionCreate(BaseModel):
    league_member_id: int
    driver_id: int
    race_id: int
    type: str
    shares: float
    price_per_share: float
    total_value: float


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_member_id: int
    driver_id: int
    race_id: int
    type: str
    shares: float
    price_per_share: float
    total_value: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Race results
# ---------------------------------------------------------------------------
class RaceResultCreate(BaseModel):
    driver_id: int
    race_id: int
    finish_position: int
    fantasy_points: float


class RaceResultUpdate(BaseModel):
    finish_position: int | None = None
    fantasy_points: float | None = None


class RaceResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    driver_id: int
    race_id: int
    finish_position: int
    fantasy_points: float


# ---------------------------------------------------------------------------
# Matchups
# ---------------------------------------------------------------------------
class MatchupCreate(BaseModel):
    league_id: int
    race_id: int
    home_member_id: int
    away_member_id: int
    type: str
    home_points: float | None = None
    away_points: float | None = None
    winner_member_id: int | None = None
    knockout_round: int | None = None


class MatchupUpdate(BaseModel):
    home_points: float | None = None
    away_points: float | None = None
    winner_member_id: int | None = None
    knockout_round: int | None = None


class MatchupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    league_id: int
    race_id: int
    home_member_id: int
    away_member_id: int
    type: str
    home_points: float | None = None
    away_points: float | None = None
    winner_member_id: int | None = None
    knockout_round: int | None = None