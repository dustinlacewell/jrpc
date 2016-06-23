from autobahn.websocket.protocol import createWsUrl
from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketClientFactory


class JRPCFactory(object):
    """
    Factory mixin for hosting a JRPC peer. Takes a JRPCProtocol.
    Supports passing a dispatch dictionary. If no dispatch
    is provided the protocol itself is used for gathering
    methods that begin with "do".
    """

    def __init__(self, host, *args, **kwargs):
        self.dispatch = kwargs.pop('dispatch', {})
        port = kwargs.pop('port', 9000)
        wsUrl = createWsUrl(host, port)
        super(JRPCFactory, self).__init__(wsUrl, *args, **kwargs)

    def buildProtocol(self, addr):
        p = self.protocol(self.dispatch)
        p.factory = self
        return p


class JRPCServerFactory(JRPCFactory, WebSocketServerFactory):
    pass


class JRPCClientFactory(JRPCFactory, WebSocketClientFactory):
    pass
