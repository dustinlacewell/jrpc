import json
from copy import copy

from zope.interface import implementer

from twisted.internet import reactor, defer
from twisted.internet.error import ConnectError
from twisted.web.iweb import IAgentEndpointFactory
from twisted.web.client import HTTPConnectionPool
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol, Factory
from twisted.web.client import ResponseDone
from twisted.internet.endpoints import UNIXClientEndpoint
from twisted.web.client import Agent

import treq


def _remove_empty(params):
    params = params or {}
    clean_params = copy(params)
    for key, val in params.iteritems():
        if val is None:
            del clean_params[key]
    return clean_params

@implementer(IAgentEndpointFactory)
class DockerEndpointFactory(object):
    """
    Connect to Docker's Unix socket.
    """
    def __init__(self, reactor, socket=b'/var/run/docker.sock'):
        self.reactor = reactor
        self.socket = socket

    def endpointForURI(self, uri):
        return UNIXClientEndpoint(self.reactor, self.socket)

class _Reader(Protocol):
    def __init__(self, streamHandler):
        self.streamHandler = streamHandler
        self.finished = Deferred()

    def dataReceived(self, data):
        result = self.streamHandler(data.decode('utf8', 'ignore'))
        if result != None:
            self.transport.loseConnection()

    def connectionLost(self, reason):
        if reason.check(ResponseDone):
            self.finished.callback(None)
            return
        self.finished.errback(reason)

    def listen(self, response):
        d = Deferred()
        response.deliverBody(self)
        return d

class Client(object):
    """A minimal Docker API client
    """

    pool = None

    def __init__(self, host, version="1.17", timeout=None, pool=None):
        self.version = version
        self.timeout = timeout
        self.pool = pool or HTTPConnectionPool(reactor, persistent=False)
        self.client = self._init_client(host)

    def _init_client(self, uri):
        if uri.startswith('docker://'):
            self.host = "unix://localhost"
            socket = uri[9:]
            print("Binding to Docker {} on {}".format(self.host, socket))

            ep_factory = DockerEndpointFactory(reactor, socket)
            agent = Agent.usingEndpointFactory(reactor, ep_factory)
        else:
            self.host = uri
            agent = Agent(reactor, pool=self.pool)
        return treq.client.HTTPClient(agent)


    def assert_code(self, code, message):
        if 400 <= code < 500:
            print(u"Assertion failure: {}:{}".format(code, message))
            raise RuntimeError('{} Client Error: {}'.format(code, message))

        elif 500 <= code < 600:
            print(u"Assertion failure: {}:{}".format(code, message))
            raise RuntimeError('{} Server Error: {}'.format(code, message))

    def _make_url(self, method):
        return "{}/v1.17/{}".format(self.host, method)


    def request(self, method, path, **kwargs):
        kwargs = copy(kwargs)
        kwargs['params'] = _remove_empty(kwargs.get('params'))
        kwargs['pool'] = self.pool

        post_json = kwargs.pop('post_json', False)
        if post_json:
            headers = kwargs.setdefault('headers', {})
            headers['Content-Type'] = ['application/json']
            kwargs['data'] = json.dumps(kwargs['data'])

        kwargs['url'] = self._make_url(path)
        expect_json = kwargs.pop('expect_json', True)

        d = method(**kwargs)

        def content(response):
            content = []
            cd = treq.collect(response, content.append)
            cd.addCallback(lambda _: u''.join(content).decode('utf8', 'ignore'))
            cd.addCallback(done, response)
            return cd

        def done(content, response):
            self.assert_code(response.code, content)
            if expect_json:
                content = json.loads(content)
            return content

        def err(failure):
            failure.trap(ConnectError)
            raise ConnectError('Could not establish a connection to Docker socket or host.')

        d.addCallbacks(content, err)
        return d

    def get(self, path, **kwargs):
        return self.request(self.client.get, path, **kwargs)

    def post(self, path, **kwargs):
        return self.request(self.client.post, path, **kwargs)

    def delete(self, path, **kwargs):
        kwargs['v'] = 1
        return self.request(self.client.delete, path, **kwargs)

    def logs(self, container, streamHandler=None, **kwargs):
        params = {
            'stdout': 1,
            'stderr': 1,
            'follow': 1,
            'tail': 500,
        }

        result = Deferred()

        url = 'containers/{}/logs'.format(container)
        url = self._make_url(url)
        d = self.client.get(url=url, params=params)

        def finished(d):
            result.callback(None)

        d.addCallback(_Reader(streamHandler).listen)
        d.addCallback(finished)
        return result

    def containers(self,
                   quiet=False, all=False, trunc=True, latest=False,
                   since=None, before=None, limit=-1, pretty=False,
                   running=None, image=None):
        params = {
            'limit': 1 if latest else limit,
            'only_ids': 1 if quiet else 0,
            'all': 1 if all else 0,
            'trunc_cmd': 1 if trunc else 0,
            'since': since,
            'before': before
        }
        return self.get('containers/ps', params=params)

    def events(self, streamHandler):
        url = 'events'
        url = self._make_url(url)
        d = self.client.get(url=url, params={})

        result = Deferred()
        def finished(d):
            result.callback(None)

        def on_content(line):
            streamHandler(json.loads(line))

        d.addCallback(_Reader(on_content).listen)
        d.addCallback(finished)
        return result
