import os

from twisted.application import internet, service
from twisted.web.static import File
from twisted.web.server import Site

from jrpc import JRPCServerService, JRPCServerProtocol

WS_HOST = os.environ.get('WS_HOST', 'localhost')
WS_PORT = os.environ.get('WS_PORT', 9000)

class TemplateProtocol(JRPCServerProtocol):
   def doEcho(self, msg):
       return msg

# create the Application
application = app = service.Application("template")

# create the RPC Server
templateService = JRPCServerService(TemplateProtocol, WS_HOST, WS_PORT)
templateService.setServiceParent(app)

# create the Web Server
root = File(os.path.dirname(__file__))
webService = internet.TCPServer(8080, Site(root))
webService.setServiceParent(app)


