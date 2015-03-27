import os, sys

sys.path.append(os.path.dirname(__file__))

from twisted.application import internet, service
from twisted.web.static import File
from twisted.web.server import Site

from jrpc import JRPCServerService, JRPCServerProtocol

from .docker import Client

WS_HOST = os.environ.get('WS_HOST', 'localhost')
WS_PORT = os.environ.get('WS_PORT', 9000)

dc = Client('docker:///var/run/docker.sock')

class DockerProtocol(JRPCServerProtocol):

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


application = app = service.Application("docker")

dockerService = JRPCServerService(DockerProtocol, WS_HOST, WS_PORT)
dockerService.setServiceParent(app)

root = File(os.path.dirname(__file__))
webService = internet.TCPServer(8080, Site(root))
webService.setServiceParent(app)
