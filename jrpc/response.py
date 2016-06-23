import json


class JRPCResponse(object):
    """
    Represents the result of an executed RPC method request.
    The id is used to match the result with the original
    request. If the error attribute is not None the result
    will contain the details of the failure.
    """

    def __init__(self, id, result=None, error=None):
        # the id of the corresponding request
        self.id = id
        # the result of the RPC request
        self.result = result
        # the error type if any
        self.error = error

    def data(self):
        '''return dictionary representation of the response'''
        return {'id': self.id, 'result': self.result, 'error': self.error, }

    def json(self):
        '''return json representation of the response'''
        return json.dumps(self.data())

    def __str__(self):
        s = self.result
        if self.error:
            s = "{}:{}".format(self.error, self.result)
        return str(s)

    @classmethod
    def from_json(cls, json_str):
        '''create JRPCResponse from json'''
        obj = json.loads(json_str)
        return cls(obj['id'], obj.get('result'), obj.get('error'))
