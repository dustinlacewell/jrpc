import json, collections

from twisted.internet.defer import maybeDeferred, Deferred

from autobahn.websocket.protocol import createWsUrl
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory

from jrpc.dispatcher import Dispatcher


class JRPCRequest(object):
    """
    Represents the intention to invoke an RPC method whether
    locally or remotely. A request with an id of None will
    not recieve a result and will not increment request
    counters.
    """
    def __init__(self, method, args=None, kwargs=None, id=None):
        # the name of the method to invoke
        self.method = method
        # positional arguments
        self.args = args or tuple()
        # keyword arguments
        self.kwargs = kwargs or dict()
        # id representing the request
        self.id = id

    def data(self):
        '''return dictionary representation of the request'''
        return {
            'method': self.method,
            'args': self.args,
            'kwargs': self.kwargs,
            'id': self.id
        }

    def json(self):
        '''return json representation of the request'''
        return json.dumps(self.data())

    @classmethod
    def from_json(cls, json_str):
        '''create a JRPCRequest from json'''
        obj = json.loads(json_str)
        return cls(obj['method'],
                   obj.get('args', tuple()),
                   obj.get('kwargs', dict()),
                   obj.get('id', None))

class JRPCResponse(object):
    """
    Represents the result of an executed RPC method request.
    The id is used to match the result with the original
    request. If the error attribute is not None the result
    will contain the details of the failure.
    """

    def __init__(self, id, result=None, error=None):
        # the id of the corresponding request
        self.id = id
        # the result of the RPC request
        self.result = result
        # the error type if any
        self.error = error

    def data(self):
        '''return dictionary representation of the response'''
        return {
            'id': self.id,
            'result': self.result,
            'error': self.error,
        }

    def json(self):
        '''return json representation of the response'''
        return json.dumps(self.data())

    @classmethod
    def from_json(cls, json_str):
        '''create JRPCResponse from json'''
        obj = json.loads(json_str)
        return cls(obj['id'],
                   obj.get('result'),
                   obj.get('error'))

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
        Message may either be remote reqeusts for local
        method invocation or the result of our own requests.
        """
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        try:
            request = JRPCRequest.from_json(payload)
        except Exception as e:
            print "Payload exception:", e
        else:
            return self.handle_request(request)

        try:
            response = JRPCResponse.from_json(payload)
        except Exception as e:
            print "Payload exception:", e
        else:
            return self.handle_response(response)

        print "Couldn't interpret payload!"

    def handle_request(self, request):
        """
        Handle an incomming request to call a local method.
        If the request contains an id attach callbacks to
        the resulting deferred object to that it may be
        handed back to the requesting peer.
        """
        handler = self.dispatcher[request.method]
        if request.id != None:
            print "ID detected."
            d = maybeDeferred(handler, *request.args, **request.kwargs)
            d.addCallback(self.return_response, request.id)
            d.addErrback(self.return_error, request.id)
        else:
            handler(*request.args, **request.kwargs)

    def return_response(self, result, id):
        """
        Return a response back to the peer.
        """
        print "Returning result response for:", id
        print "Result:", result
        response = JRPCResponse(id, result=result)
        self.protocol.sendMessage(response.json())

    def return_error(self, failure, id):
        """
        Return an error back to the peer.
        """
        response = JRPCResponse(id,
                                result=failure.getErrorMessage(),
                                error=str(failure.type))
        self.protocol.sendMessage(response.json())

    def handle_response(self, response):
        """
        Handle a response to a previously requested remote
        method call.
        """
        d = self.requests.pop(response.id)
        if response.error:
            d.errback(response.result)
        else:
            d.callback(response.result)


class JRPCProtocol(WebSocketServerProtocol):
    """
    This class is the main protocol for handling interaction with
    a remote JRPC peer. It features a simple interface for making
    both fire-and-forget invocations but also requests that will
    result in a response in the form of a deferred object.

    To provide callable methods for peers to invoke, subclasses
    can implement methods beginning with the token "do" which
    will make them automatically available.
    """
    def __init__(self, dispatch):
        self.dispatch = dispatch
        self.manager = JRPCManager(self, Dispatcher(self))

    def onConnect(self, peer):
        print "Websocket connected to peer: {}".format(peer)

    def onMessage(self, payload, isBinary):
        print "Payload recieved: ", payload
        # hand the message to the rpc manager
        self.manager.handle(payload)

    def request(self, *args, **kwargs):
        return self.manager.call(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self.manager.invoke(*args, **kwargs)


class JRPCServerFactory(WebSocketServerFactory):
    """
    Factory for hosting a JRPC server. Takes a JRPCProtocol.
    Supports passing a dispatch dictionary. If no dispatch
    is provided the protocol itself is used for gathering
    methods that begin with "do".
    """

    protocol = JRPCProtocol

    def __init__(self, host, *args, **kwargs):
        self.dispatch = kwargs.pop('dispatch', {})
        port = kwargs.pop('port', 9000)
        wsUrl = createWsUrl(host, port)
        WebSocketServerFactory.__init__(self, wsUrl, *args, **kwargs)


    def buildProtocol(self, addr):
        p = self.protocol(self.dispatch)
        p.factory = self
        if not self.dispatch:
            p.dispatch = Dispatcher(p)
        return p
