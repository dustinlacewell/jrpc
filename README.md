
JSON RPC over WebSockets
========================

`jrpc` is a module built ontop of [Twisted](https://twistedmatrix.com/trac/) and [Autobahn](http://autobahn.ws/) for creating [websocket](https://developer.mozilla.org/en-US/docs/WebSockets) servers and clients that
speak a simple two-way [RPC](http://en.wikipedia.org/wiki/Remote_procedure_call) protocol over [JSON](http://en.wikipedia.org/wiki/JSON). A corresponding [Javascript library is provided](https://github.com/dustinlacewell/jrpc/blob/master/jrpc.js) for
easy integration into web front-ends.


Quickstart
----------

To quickly demonstrate some of the capabilities of the system the following commands should get you up and running with a demo:

    git clone https://github.com/dustinlacewell/jrpc.git
    cd jrpc
    python setup.py
    twistd -noy examples/math/math.tac

At this point should be able to browse to [http://localhost:8080/](http://localhost:8080/) and interact with a [simple calculator demo](https://github.com/dustinlacewell/jrpc/blob/master/examples/math/index.html) that does its calculations by [calling remote methods on a server](https://github.com/dustinlacewell/jrpc/blob/master/examples/math/math.tac) running on port 9000.

### Docker

*Alternatively*, if you have [Docker](https://www.docker.com/) installed you can test this out with a single command by running [a premade image](https://registry.hub.docker.com/u/dlacewell/jrpc/) available on the DockerHub. By default it will run the [math/math.tac example](https://github.com/dustinlacewell/jrpc/tree/master/examples/math):

    docker run -it --rm -p 8080:8080 -p 9000:9000 dlacewell/jrpc

You can also build the image yourself from your local checkout of the source:

    git clone https://github.com/dustinlacewell/jrpc.git
    cd jrpc
    docker build -t jrpc .
    docker run -it --rm -p 8080:8080 -p 9000:9000 dlacewell/jrpc


Request Specification
---------------------

[Requests](https://github.com/dustinlacewell/jrpc/blob/master/jrpc/request.py) are small objects with the following schema:

* `method` - the name of the remote method to call
* `args` - a list of positional arguments
* `kwargs` - an object containing keyword arguments
* `id` - an optional request ID

**Requests that include** a non-null `id` property indicate that the server should return a corresponding Response with the result of the remote method call. 

**Requests that omit** or set the `id` property to `null` signal to the server that it should not bother with a sending response that the client is not interested in. Even if the call results in a failure no response will be delivered.


Response Specification
----------------------

[Responses](https://github.com/dustinlacewell/jrpc/blob/master/jrpc/response.py) are returned to the caller for Requests made with a non-null `id`. The response will contain the result of a remote method call. It has the following properties:

* `id` - the id matching the corresponding request
* `result` - the result of the request
* `error` - optional error type

**If the call was successful**, the `error` attribute will be omitted or `null`.

**If the call resulted in a failure**, the `error` attribute will contain the type of the failure and the `result` property will contain details of the failure.


Protocol Creation
---------------------

There are [two main base-classes](https://github.com/dustinlacewell/jrpc/blob/master/jrpc/protocol.py) that user-code should use to implement customized RPC interfaces. One for servers, `jrpc.JRPCServerProtocol` and one for clients, `jrpc.JRPCClientProtocol`. *Both base classes work exactly the same way.*

Both base-classes feature two methods, `request` and `invoke`, both of which are used to call methods on the remote JRPC peer:

* `request` will return a Deferred which fires with the result of the call
* `invoke` will return None. There is no corresponding result response.

When using either base-class, any method who's name begins with the prefix `do` will automatically be made available as an RPC method. RPC methods may [return a Deferred](https://twistedmatrix.com/documents/current/core/howto/defer.html) or a direct result.

*Remember: The result may or may not be returned to the caller depending on what kind of request the caller made.*

Here is an example of a simple `JRPCServerProtocol` that implements some mathematical functions:

```python
from jrpc import JRPCServerProtocol

class MathProtocol(JRPCServerProtocol):
    def doAdd(self, a, b):
        return float(a) + float(b)

    def doSubtract(self, a, b):
        return float(a) - float(b)

    def doMultiply(self, a, b):
        return float(a) * float(b)

    def doDivide(self, a, b):
        return float(a) / float(b)
```

Each method starting with `do` will be exported to the available RPC interface. The `do` prefix is removed, so, `doAdd` is exported as `Add` and so on.

In the case that a peer calls `Divide` with `0` as the second parameter, or any other failure condition arises during the call, the result will contain an `error` property designating the type of the failure. In this case the `result` property will contain details of the failure.


Booting the Server
------------------

To boot a server running this JRPC interface we'll create a [Twisted Service](https://twistedmatrix.com/documents/15.0.0/api/twisted.application.service.html) using [Twisted's application framework](http://twistedmatrix.com/documents/current/core/howto/application.html).

Twisted Applications start with [a generic top-level container service](https://twistedmatrix.com/documents/15.0.0/api/twisted.application.service.Application.html). By adding your own services to this root container service, they will all be properly started by the framework when your application starts. Twisted Applications are started by invoking [the command-line utility](http://twistedmatrix.com/documents/current/core/howto/basics.html) `twistd`.

The main parent service and its various child services are all setup in what's called [a tac file](http://twistedmatrix.com/documents/current/core/howto/application.html#twistd-and-tac) which is loaded by the `twistd` tool. `twistd` will look for a variable in the file `application`, which should be set to the parent container service. *(Yes, it really needs to be called "`application`", specifically)*

```python
from twisted.application import service

application = service.Application("mathservice")
```

We then create a JRPC WebSocket service configured with our `MathProtocol` to run on the specified port. We then add the new math service to the parent service.

```python
from jrpc import JRPCServerService

mathService = JRPCServerService(MathProtocol, 'localhost', 9000)
mathService.setServiceParent(application)
```

### Putting it Together

With all the pieces in place we should have a tac file called `math.tac` that looks something like the following:

```python
from twisted.application import service

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
```

At this point we can start our little JRPC WebSocket server with the `twistd` utility.

```
$ twistd -noy math.tac
2015-03-26 15:35:06-0700 [-] Log opened.
2015-03-26 15:35:06-0700 [-] twistd 15.0.0 (/opt/virtualenvs/jrpc/bin/python 2.7.6) sting up.
2015-03-26 15:35:06-0700 [-] reactor class: twisted.internet.epollreactor.EPollReactor.
2015-03-26 15:35:06-0700 [-] JRPCServerFactory starting on 9000
2015-03-26 15:35:06-0700 [-] Starting factory <jrpc.factory.JRPCServerFactory object at 0x7f4144008790>
```

### Testing the Server

To test that the server works we can use the [included jrpc utility](https://github.com/dustinlacewell/jrpc/tree/master/bin) which takes a method name and optionally positional and/or keyword arguments:

```
$ jrpc Add -a 5,10
15
```

If any sort of exception is raised on the remote side `jrpc` will display the exception information:

```
$ ./jrpc Add -a 10,Foo
TypeError:unsupported operand type(s) for +: 'int' and 'unicode'
```


Building a Web Client
---------------------

JRPC comes with a [javascript library](https://github.com/dustinlacewell/jrpc/blob/master/jrpc.js) which makes is pretty easy to create web interfaces that can communicate with your server.

We'll use the following simple html file for our interface. Just two textboxes for input, some buttons to invoke the various RPC methods available on the server, and a textbox for the output:

```html
<html>
  <body>
    <input type="textbox" id="a" />
    <input type="textbox" id="b" />
    <button type="submit" id="Add">Add</button>
    <button type="submit" id="Subtract">Subtract</button>
    <button type="submit" id="Multiply">Multiply</button>
    <button type="submit" id="Divide">Divide</button>
    <input type="textbox" id="result" />
  </body>
</html>
```

### Serving the Files

We can easily serve the web files for our interface by using twisted to start a web-server as just another service in our tac file. We tell the web-service to serve the directory that our `math.tac` and `index.html` files are in:

```python
import os

from twisted.web.static import File
from twisted.web.server import Site

root = File(os.path.dirname(__file__))
webService = internet.TCPServer(8080, Site(root))
webService.setServiceParent(application)
```

Now when we run the tac file we should see an additional service startup in the output:

```
$ twistd -noy examples/math/math.tac
2015-03-27 00:21:48-0700 [-] Log opened.
2015-03-27 00:21:48-0700 [-] twistd 15.0.0 (/opt/virtualenvs/jrpc/bin/python 2.7.6) starting up.
2015-03-27 00:21:48-0700 [-] reactor class: twisted.internet.epollreactor.EPollReactor.
2015-03-27 00:21:48-0700 [-] JRPCServerFactory starting on 9000
2015-03-27 00:21:48-0700 [-] Starting factory <jrpc.factory.JRPCServerFactory object at 0x7f45c778e310>
2015-03-27 00:21:48-0700 [-] Site starting on 8080
2015-03-27 00:21:48-0700 [-] Starting factory <twisted.web.server.Site instance at 0x7f45c7792680>
```

We can see that not only do we have our JRPC WebSocket server running on port `9000` but we also have a web server running on port `8080`. By visiting [http://localhost:8080/][http://localhost:8080] you should be able to see our simple web interface.


### Connecting it all up

Now we'll add some javascript to the page that opens a WebSocket to our JRPC server and bind the remote methods to our buttons. First we'll add [JQuery](https://jquery.com/) and the [JRPC javascript library](https://github.com/dustinlacewell/jrpc/blob/master/jrpc.js) to a new `<head></head>` section:

```html
  <head>
    <script src="//code.jquery.com/jquery-1.11.2.min.js"></script>
    <script type="text/javascript" src="jrpc.js"></script>
  </head>
```

Next we'll create a JRPC WebSocket when the page is loaded by adding a new `<script></script>` section at the end of our `<body></body>` section:

```html
    <script type="text/javascript">
      $(document).ready(function() {
        rpc = new JRPC.WebSocket(window.location.hostname, 9000);
      });
    </script>
```

If you reload the page, you should now see a message in your browser's debug console that it has established a websocket connection to the local server.

Next, we'll attach `click` handlers to all of our buttons. We'll use their `id` attribute to identify which RPC method should be called when they are clicked. We'll use the two `<input />`s as our arguments to the method call:

```html
    <script type="text/javascript">
      $(document).ready(function() {
        rpc = new JRPC.WebSocket(window.location.hostname, 9000);
        $('button').click(function(e) {
          // prevent actual form submission
          e.preventDefault();
          // grab the two input values
          var $a = $("#a").val();
          var $b = $("#b").val();
          // grab the method name from the button we clicked
          var method = $(this).attr('id');
          // invoke the remote method on the RPC server
          rpc.invoke(method, [$a, $b]);
        });
      });
    </script>
```

If we reload the page, and we can see that we're connected to the server we can input some values into the text boxes and press buttons to trigger the execution of methods running on the server. However, we are not receiving any responses with the result. `invoke` is a 'fire-and-forget' way of triggering remote methods. If we want to actually receive the result of the call we'll need to use `request` instead and provide a callback. With all the changes our `index.html` should read as follows:

```html
<!DOCTYPE html>
<html>
  <head>
    <script src="//code.jquery.com/jquery-1.11.2.min.js"></script>
    <script type="text/javascript" src="jrpc.js"></script>
  </head>
  <body>
    <input type="textbox" id="a" />
    <input type="textbox" id="b" />
    <button type="submit" id="Add">Add</button>
    <button type="submit" id="Subtract">Subtract</button>
    <button type="submit" id="Multiply">Multiply</button>
    <button type="submit" id="Divide">Divide</button>
    <input type="textbox" id="result" />
    <script type="text/javascript">
      $(document).ready(function() {
        rpc = new JRPC.WebSocket(window.location.hostname, 9000);
        $('button').click(function(e) {
          e.preventDefault();
          var $a = $("#a").val();
          var $b = $("#b").val();
          var method = $(this).attr('id');
          rpc.request(method, [$a, $b], {}, function(r) {
            $("#result").val(r.result);
          }, function(e) {
            alert(e.error + ": " + e.result);
          });
        });
      });
    </script>
  </body>
</html>
```

If we refresh the page, we can now input values and clicking on buttons will actually result in the response values showing up in the output textbox. By passing a callback to `request` we can handle what should happen when the result is returned to us. The second callback is how we can handle exceptions. Try dividing by zero to see how the error is presented as an alert.

The finished example [is available here](https://github.com/dustinlacewell/jrpc/tree/master/examples/math).


It Goes Both Ways
-----------------

You've seen how to build a simple RPC system with [very little code](https://github.com/dustinlacewell/jrpc/tree/master/examples/math) using JRPC and how your web-interfaces can call methods against a backend server. JRPC actually supports two-way invocation. By passing an object as the third parameter to `JRPC.WebSocket` you can make javascript methods available to the server. Check additional examples to how this is done.
