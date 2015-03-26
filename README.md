
JSON RPC over WebSockets
========================

`jrpc` is a module built ontop of Twisted and Autobahn for creating websocket servers that
speak a simple two-way RPC protocol over JSON. A corresponding Javascript library is provided for
easy integration into front-ends. Both endpoints support bidirectional RPC with result
callbacks.


Request Specification
---------------------

Requests are small objects with the following schema:

* `method` - the name of the remote method to call
* `args` - a list of positional arguments
* `kwargs` - an object containing keyword arguments
* `id` - an optional request ID

Requests that include an ID will eventually result in a corresponding response containing
the result of the remote method call. If a request does not contain an id or the id is
null, then no response will be returned and the request is considered a 'fire-and-forget'
invocation.

Response Specification
----------------------

Requests with an id will recieve a response with the following schema:

* `id` - the id matching the corresponding request
* `result` - the result of the request
* `error` - optional error type

The response id will identify the corresponding request. If the response has a non-null
error property, the request failed, otherwise it succeeded. In either case the result
parameter will specify the result of the call.


JRPCProtocol Creation
---------------------

The `jrpc.protocol.JRPCProtocol` class is the main class for user inheritance. It implements the handling of interaction with a remote JRPC peer.

In particular the methods `request` and `invoke` are used to call methods on the remote peer.

* `invoke` will call a remote method but will not recieve a result
* `request` will call a remote method and return a Deferred which will fire with the response from the peer.

Making methods available to remote peers is as easy as defining methods on the protocol that begin with the prefix "**do**" such as `doThis` or `doThat`. These methods may return either direct values or Deferreds. In either case the result will be sent to the remote peer based on how the peer made the request.

Here is an example of a simple JRPCProtocol that implements some mathematical functions:

    from jrpc.protocol import JRPCProtocol
    
    class MathProtocol(JRPCProtocol):
        def doAdd(self, a, b):
            return a + b
    
        def doSub(self, a, b):
            return a - b
    
        def doMultiply(self, a, b):
            return a * b
    
        def doDivide(self, a, b):
            return a / b

Each method will be exported without the "*do*" prefix such as `Add`, `Sub` and so on. In the case that a peer calls `Divide` with `0` as the second parameter, the result will contain an `error` property with the name of the Python exception and the `result` the content of the exception.


Booting the Server
------------------

To get a server running we'll create a Twisted Application using a "tac" file. The tac file is responsible for creating a module-level attribute called `application` which should be a `twisted.application.service.Application` instance. The idea is that you add services to the application and those are started and handled by the framework.

    from twisted.application import service

    application = service.Application("mathservice")

To create our service we need a factory for creating instances of our `MathProtocol` when clients connect.


    factory = JRPCServerFactory('localhost', port=9000)
    factory.protocol = MathProtocol

We can then create the service and add it to our application.

    from twisted.application import internet

    mathService = internet.TCPServer(9000, factory)
    mathService.setServiceParent(application)

At this point we can start our little JRPC WebSocket server with the `twistd` utility.

    $ twistd -noy math.tac
    2015-03-26 15:35:06-0700 [-] Log opened.
    2015-03-26 15:35:06-0700 [-] twistd 15.0.0 (/opt/virtualenvs/jrpc/bin/python 2.7.6) starting up.
    2015-03-26 15:35:06-0700 [-] reactor class: twisted.internet.epollreactor.EPollReactor.
    2015-03-26 15:35:06-0700 [-] JRPCServerFactory starting on 9000
    2015-03-26 15:35:06-0700 [-] Starting factory <jrpc.factory.JRPCServerFactory object at 0x7f4144008790>

To test that the server works we can use the include `rpc_call` utility which takes a hostname and port, method name and any arguments and makes a JRPC request.
