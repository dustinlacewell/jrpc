import os

from twisted.application import internet, service
from twisted.web.static import File
from twisted.web.server import Site

from jrpc import JRPCServerService, JRPCServerProtocol

class MathProtocol(JRPCServerProtocol):
    def doAdd(self, a, b):
        return int(a) + int(b)

    def doSubtract(self, a, b):
        return int(a) - int(b)

    def doMultiply(self, a, b):
        return int(a) * int(b)

    def doDivide(self, a, b):
        return float(a) / float(b)

application = service.Application("mathservice")

mathService = JRPCServerService(MathProtocol, 'localhost', 9000)
mathService.setServiceParent(application)

root = File(os.path.dirname(__file__))
webService = internet.TCPServer(8080, Site(root))
webService.setServiceParent(application)
