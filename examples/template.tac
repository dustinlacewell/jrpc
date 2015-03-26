import os, json, sys

sys.path.append("..")

from twisted.application import internet, service
from twisted.web.static import File
from twisted.web.server import Site

from jrpc.rpc import JRPCServerFactory, JRPCProtocol

WS_HOST = os.environ.get('WS_HOST', 'localhost')
WS_PORT = os.environ.get('WS_PORT', 9000)

class TemplateProtocol(JRPCProtocol):
    def doAdd(self, a, b):
        self.invoke('Alert', message="The result was: {}".format(a + b))


factory = JRPCServerFactory(WS_HOST, port=WS_PORT, debug=False)
factory.protocol = TemplateProtocol

# websockets logging service
wsLogService = internet.TCPServer(int(WS_PORT), factory)

# webserver
root = File('template')
wsWebService = internet.TCPServer(8080, Site(root))

# create the Application
application = app = service.Application("template")
wsLogService.setServiceParent(app)
wsWebService.setServiceParent(app)


