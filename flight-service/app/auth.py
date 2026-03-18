import grpc
from config import GRPC_API_KEY

_SKIP_AUTH_PREFIXES = (
    "/grpc.reflection.v1alpha.ServerReflection",
    "/grpc.reflection.v1.ServerReflection",
)


class ApiKeyInterceptor(grpc.ServerInterceptor):
    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method or ""
        for prefix in _SKIP_AUTH_PREFIXES:
            if method.startswith(prefix):
                return continuation(handler_call_details)
        metadata = dict(handler_call_details.invocation_metadata)
        api_key = metadata.get("x-api-key", "")
        if not GRPC_API_KEY:
            return continuation(handler_call_details)
        if api_key != GRPC_API_KEY:
            return _unauthenticated_handler
        return continuation(handler_call_details)


class _UnauthenticatedHandler(grpc.RpcMethodHandler):
    def __init__(self):
        self.request_streaming = False
        self.response_streaming = False
        self.request_deserializer = None
        self.response_serializer = None
        self.unary_unary = self._abort
        self.unary_stream = self._abort_stream
        self.stream_unary = None
        self.stream_stream = None

    @staticmethod
    def _abort(request, context):
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Invalid or missing API key")
        return None
    
    @staticmethod
    def _abort_stream(request, context):
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Invalid or missing API key")
        return None


_unauthenticated_handler = _UnauthenticatedHandler()
