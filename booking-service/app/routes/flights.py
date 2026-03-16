from fastapi import APIRouter, HTTPException, Query
import grpc

from grpc_client import search_flights, get_flight

router = APIRouter(prefix="/flights", tags=["flights"])


def _flight_to_dict(f):
    return {
        "id": f.id,
        "flight_number": f.flight_number,
        "origin": f.origin,
        "destination": f.destination,
        "departure_time": f.departure_time.ToDatetime().isoformat(),
        "arrival_time": f.arrival_time.ToDatetime().isoformat(),
        "total_seats": f.total_seats,
        "available_seats": f.available_seats,
        "price": f.price,
        "status": f.status,
    }


@router.get("")
def list_flights(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    date: str | None = Query(None),
):
    try:
        resp = search_flights(origin, destination, date)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=e.details())

    return [_flight_to_dict(f) for f in resp.flights]


@router.get("/{flight_id}")
def get_flight_by_id(flight_id: int):
    try:
        resp = get_flight(flight_id)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Flight not found")
        raise HTTPException(status_code=500, detail=e.details())

    return _flight_to_dict(resp.flight)
