from twisted.python.failure import Failure
from twisted.internet.defer import Deferred, maybeDeferred

from .request import JRPCRequest
from .response import JRPCResponse


class JRPCManager(object):
    """
    Handles the dispatching of remote requests to invoke
    local methods and the sending of requests to remote
    peers.
    """

    def __init__(self, protocol, dispatcher):
        # mapping of ids to deferreds
        self.requests = {}
        # reference back to parent protocol
        self.protocol = protocol
        # dispatch mapping of local handlers
        self.dispatcher = dispatcher
        # next request id
        self._rid = 0

    def call(self, method, *args, **kwargs):
        """
        Call a remote method and return a deferred which will
        be invoked with either the result or failure.
        """
        d = Deferred()
        self.requests[self._rid] = d
        request = JRPCRequest(method, args, kwargs, self._rid)
        self.protocol.sendMessage(request.json())
        self._rid += 1
        return d

    def invoke(self, method, *args, **kwargs):
        """
        Invoke a remote method but do not expect a result.
        """
        request = JRPCRequest(method, args, kwargs)
        self.protocol.sendMessage(request.json())

    def handle(self, payload):
        """
        Handle an incomming message from the remote peer.
        Message may either be remote requests for local
        method invocation or the result of our own requests.
        """
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        exc = None

        try:
            request = JRPCRequest.from_json(payload)
        except Exception as e:
            exc = e
        else:
            return self.handle_request(request)

        try:
            response = JRPCResponse.from_json(payload)
        except Exception as e:
            exc = e
        else:
            return self.handle_response(response)

        self.return_error(Failure(exc), None)

    def handle_request(self, request):
        """
        Handle an incomming request to call a local method.
        If the request contains an id attach callbacks to
        the resulting deferred object so that it may be
        handed back to the requesting peer.
        """
        try:
            handler = self.dispatcher[request.method]
        except KeyError:
            exception = KeyError("`{}` is not an available method.".format(
                request.method))
            self.return_error(Failure(exception), request.id)
        else:
            try:
                if request.id is not None:
                    d = maybeDeferred(handler, *request.args, **request.kwargs)
                    d.addCallback(self.return_response, request.id)
                    d.addErrback(self.return_error, request.id)
                else:
                    handler(*request.args, **request.kwargs)
            except Exception as e:
                self.return_error(Failure(e), request.id)

    def return_response(self, result, id):
        """
        Return a response back to the peer.
        """
        response = JRPCResponse(id, result=result)
        self.protocol.sendMessage(response.json())

    def return_error(self, failure, id):
        """
        Return an error back to the peer.
        """
        response = JRPCResponse(id,
                                result=failure.getErrorMessage(),
                                error=str(failure.type.__name__))
        self.protocol.sendMessage(response.json())

    def handle_response(self, response):
        """
        Handle a response to a previously requested remote
        method call.
        """
        d = self.requests.pop(response.id)
        if response.error:
            d.errback(response)
        else:
            d.callback(response)
