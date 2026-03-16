FROM python:3.12-slim

WORKDIR /app

COPY flight-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY proto/ /proto/
RUN mkdir -p /app/generated && \
    python -m grpc_tools.protoc \
        -I/proto \
        --python_out=/app/generated \
        --grpc_python_out=/app/generated \
        /proto/flight.proto && \
    touch /app/generated/__init__.py && \
    sed -i 's/^import flight_pb2/from generated import flight_pb2/' /app/generated/flight_pb2_grpc.py

COPY flight-service/app/ /app/

CMD ["python", "main.py"]
