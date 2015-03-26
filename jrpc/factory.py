from autobahn.websocket.protocol import createWsUrl
from autobahn.twisted.websocket import WebSocketServerFactory

from .protocol import JRPCProtocol
from .dispatcher import Dispatcher

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
