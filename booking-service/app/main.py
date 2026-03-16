from fastapi import FastAPI
from routes.flights import router as flights_router
from routes.bookings import router as bookings_router

app = FastAPI(title="Booking Service", version="1.0.0")

app.include_router(flights_router)
app.include_router(bookings_router)


@app.get("/health")
def health():
    return {"status": "ok"}
