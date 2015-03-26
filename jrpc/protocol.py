from autobahn.twisted.websocket import WebSocketServerProtocol

from .manager import JRPCManager
from .dispatcher import Dispatcher

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
        # hand the message to the rpc manager
        self.manager.handle(payload)

    def request(self, *args, **kwargs):
        return self.manager.call(*args, **kwargs)

    def invoke(self, *args, **kwargs):
        return self.manager.invoke(*args, **kwargs)

