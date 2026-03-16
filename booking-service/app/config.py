import os

FLIGHT_SERVICE_HOST = os.getenv("FLIGHT_SERVICE_HOST", "flight-service")
FLIGHT_SERVICE_PORT = os.getenv("FLIGHT_SERVICE_PORT", "50051")
FLIGHT_GRPC_ADDR = f"{FLIGHT_SERVICE_HOST}:{FLIGHT_SERVICE_PORT}"

DB_HOST = os.getenv("BOOKING_DB_HOST", "booking-db")
DB_PORT = os.getenv("BOOKING_DB_PORT", "5432")
DB_NAME = os.getenv("BOOKING_DB_NAME", "booking_db")
DB_USER = os.getenv("BOOKING_DB_USER", "postgres")
DB_PASS = os.getenv("BOOKING_DB_PASSWORD", "postgres")
