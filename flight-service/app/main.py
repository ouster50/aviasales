import time
from concurrent import futures
import grpc

from generated import flight_pb2_grpc
from service import FlightServiceServicer
from config import GRPC_PORT


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    flight_pb2_grpc.add_FlightServiceServicer_to_server(
        FlightServiceServicer(), server
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    print(f"Flight Service gRPC server started on port {GRPC_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    time.sleep(2)
    serve()
