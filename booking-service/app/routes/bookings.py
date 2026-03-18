import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import grpc

from database import get_connection
from grpc_client import get_flight, reserve_seats, release_reservation
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/bookings", tags=["bookings"])


class CreateBookingRequest(BaseModel):
    user_id: int
    flight_id: int
    passenger_name: str
    passenger_email: str
    seat_count: int


class BookingResponse(BaseModel):
    id: str
    user_id: int
    flight_id: int
    passenger_name: str
    passenger_email: str
    seat_count: int
    total_price: float
    status: str
    created_at: str
    updated_at: str


def _row_to_response(row) -> dict:
    return {
        "id": str(row["id"]),
        "user_id": row["user_id"],
        "flight_id": row["flight_id"],
        "passenger_name": row["passenger_name"],
        "passenger_email": row["passenger_email"],
        "seat_count": row["seat_count"],
        "total_price": float(row["total_price"]),
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


@router.post("", status_code=201)
def create_booking(body: CreateBookingRequest):
    try:
        flight_resp = get_flight(body.flight_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Flight not found")
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise HTTPException(status_code=403, detail="Service authentication failed")
        raise HTTPException(status_code=500, detail=e.details())
    flight = flight_resp.flight
    booking_id = str(uuid.uuid4())
    try:
        _ = reserve_seats(body.flight_id, body.seat_count, booking_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
            raise HTTPException(status_code=409, detail="Not enough seats available")
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Flight not found")
        if e.code() == grpc.StatusCode.FAILED_PRECONDITION:
            raise HTTPException(status_code=400, detail=e.details())
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise HTTPException(status_code=403, detail="Service authentication failed")
        raise HTTPException(status_code=500, detail=e.details())
    total_price = Decimal(str(flight.price)) * body.seat_count
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO bookings
                       (id, user_id, flight_id, passenger_name,
                        passenger_email, seat_count, total_price, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, 'CONFIRMED')
                   RETURNING *""",
                (
                    booking_id,
                    body.user_id,
                    body.flight_id,
                    body.passenger_name,
                    body.passenger_email,
                    body.seat_count,
                    str(total_price),
                ),
            )
            row = cur.fetchone()
        conn.commit()
        return _row_to_response(row)
    except Exception as e:
        conn.rollback()
        try:
            release_reservation(booking_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("/{booking_id}")
def get_booking(booking_id: str):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
        return _row_to_response(row)
    finally:
        conn.close()


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM bookings WHERE id = %s FOR UPDATE",
                (booking_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Booking not found")
            if row["status"] != "CONFIRMED":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel booking in status {row['status']}",
                )
            try:
                release_reservation(booking_id)
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.NOT_FOUND:
                    raise HTTPException(status_code=500, detail=e.details())
            cur.execute(
                """UPDATE bookings
                   SET status = 'CANCELLED', updated_at = NOW()
                   WHERE id = %s
                   RETURNING *""",
                (booking_id,),
            )
            updated = cur.fetchone()
        conn.commit()
        return _row_to_response(updated)
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.get("")
def list_bookings(user_id: int = Query(...)):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM bookings WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
        return [_row_to_response(r) for r in rows]
    finally:
        conn.close()
