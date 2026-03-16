import grpc

from generated import flight_pb2, flight_pb2_grpc
from config import FLIGHT_GRPC_ADDR


def _get_stub():
    channel = grpc.insecure_channel(FLIGHT_GRPC_ADDR)
    return flight_pb2_grpc.FlightServiceStub(channel)


def search_flights(origin: str, destination: str, date: str | None = None):
    stub = _get_stub()
    request = flight_pb2.SearchFlightsRequest(
        origin=origin,
        destination=destination,
        date=date or "",
    )
    response = stub.SearchFlights(request)
    return response


def get_flight(flight_id: int):
    stub = _get_stub()
    request = flight_pb2.GetFlightRequest(id=flight_id)
    response = stub.GetFlight(request)
    return response


def reserve_seats(flight_id: int, seat_count: int, booking_id: str):
    stub = _get_stub()
    request = flight_pb2.ReserveSeatsRequest(
        flight_id=flight_id,
        seat_count=seat_count,
        booking_id=booking_id,
    )
    response = stub.ReserveSeats(request)
    return response


def release_reservation(booking_id: str):
    stub = _get_stub()
    request = flight_pb2.ReleaseReservationRequest(booking_id=booking_id)
    response = stub.ReleaseReservation(request)
    return response
