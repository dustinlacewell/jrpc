from twisted.internet import reactor
from twisted.application.internet import TCPClient, TCPServer
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint

from .request import JRPCRequest
from .response import JRPCResponse
from .protocol import JRPCClientProtocol, JRPCServerProtocol
from .factory import JRPCClientFactory, JRPCServerFactory
from .dispatcher import Dispatcher


def _buildPeerService(host, port, protocol, factory, service):
    factory = factory(host, port=port)
    factory.protocol = protocol
    return service(port, factory)


def JRPCClientService(protocol, host='localhost', port=9000):
    return _buildPeerService(host, port, protocol, JRPCClientFactory,
                             TCPClient)


def JRPCServerService(protocol, host='localhost', port=9000):
    return _buildPeerService(host, port, protocol, JRPCServerFactory,
                             TCPServer)


def JRPCClientEndpoint(protocol, host='localhost', port=9000):
    endpoint = TCP4ClientEndpoint(reactor, host, port)
    factory = JRPCClientFactory(host, port=port)
    factory.protocol = protocol
    return endpoint.connect(factory)


def JRPCServerEndpoint(protocol, host='localhost', port=9000):
    endpoint = TCP4ServerEndpoint(reactor, host, port)
    factory = JRPCClientFactory(host, port=port)
    factory.protocol = protocol
    return endpoint.connect(factory)


__all__ = [
    'JRPCRequest',
    'JRPCResponse',
    'JRPCClientProtocol',
    'JRPCServerProtocol',
    'JRPCClientFactory',
    'JRPCServerFactory',
    'Dispatcher',
]
