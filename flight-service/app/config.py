import os

GRPC_PORT = os.getenv("GRPC_PORT", "50051")

DB_HOST = os.getenv("FLIGHT_DB_HOST", "flight-db")
DB_PORT = os.getenv("FLIGHT_DB_PORT", "5432")
DB_NAME = os.getenv("FLIGHT_DB_NAME", "flight_db")
DB_USER = os.getenv("FLIGHT_DB_USER", "postgres")
DB_PASS = os.getenv("FLIGHT_DB_PASSWORD", "postgres")
