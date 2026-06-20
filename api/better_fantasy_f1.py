from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from api.routers import (
    drivers,
    users,
    leagues,
    league_members,
    races,
    driver_prices,
    portfolio_holdings,
    transactions,
    race_results,
    matchups,
)

app = FastAPI(title="Better Fantasy F1")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Turn database constraint violations into a clean 409 instead of a 500.

    This fires whenever a write breaks a database rule — most commonly a
    duplicate value on a unique column (e.g. reusing a driver_number), but also
    a foreign key pointing at a row that doesn't exist. The session's `with`
    block has already rolled back by the time we get here.
    """
    return JSONResponse(
        status_code=409,
        content={"detail": "This request conflicts with existing data "
                           "(a duplicate value, or a reference to something that doesn't exist)."},
    )


app.include_router(users.router)
app.include_router(leagues.router)
app.include_router(league_members.router)
app.include_router(drivers.router)
app.include_router(races.router)
app.include_router(driver_prices.router)
app.include_router(portfolio_holdings.router)
app.include_router(transactions.router)
app.include_router(race_results.router)
app.include_router(matchups.router)


@app.get("/health")
def health():
    return {"status": "ok"}