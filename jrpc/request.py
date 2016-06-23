import json


class JRPCRequest(object):
    """
    Represents the intention to invoke an RPC method whether
    locally or remotely. A request with an id of None will
    not recieve a result and will not increment request
    counters.
    """

    def __init__(self, method, args=None, kwargs=None, id=None):
        # the name of the method to invoke
        self.method = method
        # positional arguments
        self.args = args or tuple()
        # keyword arguments
        self.kwargs = kwargs or dict()
        # id representing the request
        self.id = id

    def data(self):
        '''return dictionary representation of the request'''
        return {
            'method': self.method,
            'args': self.args,
            'kwargs': self.kwargs,
            'id': self.id
        }

    def json(self):
        '''return json representation of the request'''
        return json.dumps(self.data())

    @classmethod
    def from_json(cls, json_str):
        '''create a JRPCRequest from json'''
        obj = json.loads(json_str)
        return cls(obj['method'], obj.get('args', tuple()),
                   obj.get('kwargs', dict()), obj.get('id', None))
