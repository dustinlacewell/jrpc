from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketClientProtocol

from .manager import JRPCManager
from .dispatcher import Dispatcher


class JRPCProtocol(object):
    """
    This class is the main protocol for handling interaction with
    a remote JRPC peer. It features a simple interface for making
    both fire-and-forget invocations but also requests that will
    result in a response in the form of a deferred object.

    To provide callable methods for peers to invoke, subclasses
    can implement methods beginning with the token "do" which
    will make them automatically available.
    """

    def __init__(self, dispatch=None):
        super(JRPCProtocol, self).__init__()
        self.manager = JRPCManager(self, dispatch or Dispatcher(self))

    def onMessage(self, payload, isBinary):
        self.manager.handle(payload)

    def request(self, *args, **kwargs):
        return self.manager.call(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self.manager.invoke(*args, **kwargs)


class JRPCServerProtocol(JRPCProtocol, WebSocketServerProtocol):
    pass


class JRPCClientProtocol(JRPCProtocol, WebSocketClientProtocol):
    pass
