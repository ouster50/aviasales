import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import grpc
from datetime import datetime, timezone
from google.protobuf.timestamp_pb2 import Timestamp
from psycopg2.extras import RealDictCursor

from generated import flight_pb2, flight_pb2_grpc
from database import get_connection


STATUS_MAP = {
    'SCHEDULED':  flight_pb2.FLIGHT_STATUS_SCHEDULED,
    'DEPARTED':   flight_pb2.FLIGHT_STATUS_DEPARTED,
    'CANCELLED':  flight_pb2.FLIGHT_STATUS_CANCELLED,
    'COMPLETED':  flight_pb2.FLIGHT_STATUS_COMPLETED,
}

RESERVATION_STATUS_MAP = {
    'ACTIVE':   flight_pb2.RESERVATION_STATUS_ACTIVE,
    'RELEASED': flight_pb2.RESERVATION_STATUS_RELEASED,
    'EXPIRED':  flight_pb2.RESERVATION_STATUS_EXPIRED,
}


def _dt_to_ts(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc))
    return ts


def _row_to_flight(row) -> flight_pb2.FlightInfo:
    return flight_pb2.FlightInfo(
        id=row['id'],
        flight_number=row['flight_number'],
        origin=row['origin'],
        destination=row['destination'],
        departure_time=_dt_to_ts(row['departure_time']),
        arrival_time=_dt_to_ts(row['arrival_time']),
        total_seats=row['total_seats'],
        available_seats=row['available_seats'],
        price=float(row['price']),
        status=STATUS_MAP.get(row['status'], flight_pb2.FLIGHT_STATUS_UNSPECIFIED),
    )


class FlightServiceServicer(flight_pb2_grpc.FlightServiceServicer):
    def SearchFlights(self, request, context):
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT * FROM flights
                    WHERE origin = %s
                      AND destination = %s
                      AND status = 'SCHEDULED'
                """
                params = [request.origin, request.destination]
                if request.date:
                    query += " AND CAST(departure_time AS DATE) = %s"
                    params.append(request.date)
                query += " ORDER BY departure_time"
                cur.execute(query, params)
                rows = cur.fetchall()
            return flight_pb2.SearchFlightsResponse(
                flights=[_row_to_flight(r) for r in rows]
            )
        finally:
            conn.close()

    def GetFlight(self, request, context):
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM flights WHERE id = %s", (request.id,))
                row = cur.fetchone()
            if not row:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Flight {request.id} not found")
                return flight_pb2.GetFlightResponse()
            return flight_pb2.GetFlightResponse(flight=_row_to_flight(row))
        finally:
            conn.close()

    def ReserveSeats(self, request, context):
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM flights WHERE id = %s FOR UPDATE",
                    (request.flight_id,),
                )
                flight = cur.fetchone()
                if not flight:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(f"Flight {request.flight_id} not found")
                    conn.rollback()
                    return flight_pb2.ReserveSeatsResponse()
                if flight['status'] != 'SCHEDULED':
                    context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                    context.set_details("Flight is not in SCHEDULED status")
                    conn.rollback()
                    return flight_pb2.ReserveSeatsResponse()
                if flight['available_seats'] < request.seat_count:
                    context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
                    context.set_details(
                        f"Not enough seats: requested {request.seat_count}, "
                        f"available {flight['available_seats']}"
                    )
                    conn.rollback()
                    return flight_pb2.ReserveSeatsResponse()
                cur.execute(
                    """UPDATE flights
                       SET available_seats = available_seats - %s,
                           updated_at = NOW()
                       WHERE id = %s""",
                    (request.seat_count, request.flight_id),
                )
                cur.execute(
                    """INSERT INTO seat_reservations
                           (flight_id, booking_id, seat_count, status)
                       VALUES (%s, %s, %s, 'ACTIVE')
                       RETURNING id""",
                    (request.flight_id, request.booking_id, request.seat_count),
                )
                reservation_id = cur.fetchone()['id']
            conn.commit()
            return flight_pb2.ReserveSeatsResponse(
                reservation_id=reservation_id,
                status=flight_pb2.RESERVATION_STATUS_ACTIVE,
            )
        except Exception as e:
            conn.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return flight_pb2.ReserveSeatsResponse()
        finally:
            conn.close()

    def ReleaseReservation(self, request, context):
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT sr.*, f.id AS fid
                       FROM seat_reservations sr
                       JOIN flights f ON sr.flight_id = f.id
                       WHERE sr.booking_id = %s AND sr.status = 'ACTIVE'
                       FOR UPDATE""",
                    (request.booking_id,),
                )
                reservation = cur.fetchone()
                if not reservation:
                    context.set_code(grpc.StatusCode.NOT_FOUND)
                    context.set_details(
                        f"Active reservation for booking {request.booking_id} not found"
                    )
                    conn.rollback()
                    return flight_pb2.ReleaseReservationResponse(success=False)
                cur.execute(
                    """UPDATE flights
                       SET available_seats = available_seats + %s,
                           updated_at = NOW()
                       WHERE id = %s""",
                    (reservation['seat_count'], reservation['flight_id']),
                )
                cur.execute(
                    """UPDATE seat_reservations
                       SET status = 'RELEASED', updated_at = NOW()
                       WHERE id = %s""",
                    (reservation['id'],),
                )
            conn.commit()
            return flight_pb2.ReleaseReservationResponse(success=True)
        except Exception as e:
            conn.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return flight_pb2.ReleaseReservationResponse(success=False)
        finally:
            conn.close()
