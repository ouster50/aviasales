import time
from concurrent import futures
import grpc

from generated import flight_pb2, flight_pb2_grpc
from service import FlightServiceServicer
from auth import ApiKeyInterceptor
from config import GRPC_PORT, GRPC_API_KEY


def serve():
    interceptors = [ApiKeyInterceptor()]
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=interceptors
    )
    flight_pb2_grpc.add_FlightServiceServicer_to_server(
        FlightServiceServicer(), server
    )
    try:
        from grpc_reflection.v1alpha import reflection

        service_names = (
            flight_pb2.DESCRIPTOR.services_by_name['FlightService'].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)
        print("gRPC reflection: ENABLED")
    except ImportError:
        print("gRPC reflection: DISABLED (grpcio-reflection not installed)")
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    server.start()
    print(f"Flight Service gRPC server started on port {GRPC_PORT}")
    print(f"API Key authentication: {"ENABLED" if GRPC_API_KEY else "DISABLED"}")
    server.wait_for_termination()


if __name__ == "__main__":
    time.sleep(2)
    serve()
