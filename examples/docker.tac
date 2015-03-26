import os, json, sys

sys.path.append("..")

from twisted.application import internet, service
from twisted.web.static import File
from twisted.web.server import Site

from jrpc.rpc import JRPCServerFactory, JRPCProtocol

from .docker import Client

WS_HOST = os.environ.get('WS_HOST', 'localhost')
WS_PORT = os.environ.get('WS_PORT', 9000)

dc = Client('docker:///var/run/docker.sock')

class DockerProtocol(JRPCProtocol):

    cid = None

    def invokeRefresh(self, containers):
        '''update client with new container data'''
        self.invoke('Refresh', containers=containers)

    def handleEvent(self, event):
        '''if docker emits a container event update the client'''
        if event['status'] in ['die', 'start', 'destroy']:
            self.doRefresh().addCallback(self.invokeRefresh)

    def onOpen(self):
        '''when we connect start listening to docker events and update the containers'''
        dc.events(self.handleEvent)
        self.doRefresh().addCallback(self.invokeRefresh)

    def doRefresh(self):
        '''get current containers'''
        return dc.containers(all=True)

    def doAttach(self, cid):
        '''attach to a container and pass them to client as logs events come in'''
        def cb(msg):
            if cid != self.cid:
                return
            self.invoke('Log', message=msg)

        dc.logs(cid, cb)
        self.cid = cid


factory = JRPCServerFactory(WS_HOST, port=WS_PORT, debug=False)
factory.protocol = DockerProtocol

# websockets logging service
wsLogService = internet.TCPServer(int(WS_PORT), factory)

# webserver
root = File('docker')
wsWebService = internet.TCPServer(8080, Site(root))

# create the Application
application = app = service.Application("docker")
wsLogService.setServiceParent(app)
wsWebService.setServiceParent(app)


