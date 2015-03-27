var JRPC = JRPC || function(){

var JRPC = {};

var make_endpoint = function(host, port) {
    return "ws://" + host + ":" + port;
};


// JRPC.Request
// Represents the intention to invoke an RPC method
// whether locally or remotely. A request with a
// null id will not receive a result and will not
// increment request counters.
JRPC.Request = function(method, args, kwargs, id) {
    // the name of the method to call
    this.method = method;
    // array of positional arguments
    this.args = args;
    // object of keyword arguments
    this.kwargs = kwargs;
    // id representing the request
    this.id = id;
}

JRPC.Request.prototype.data = function() {
    // Return an object containing the deatails
    // of the request.
    return {
        method: this.method,
        args: this.args,
        kwargs: this.kwargs,
        id: this.id,
    };
};

JRPC.Request.prototype.json = function() {
    // return a json representation of the request
    return JSON.stringify(this.data());
};


// JRPC.Response
// Represents the result of an executed RPC method
// request. The id is used to match the result
// with the original request. If the error
// attribute is not null the result will
// contain the details of the failure.
JRPC.Response = function(id, result, error) {
    // the id of the corresponding request
    this.id = id;
    // the result of the RPC request
    this.result = result;
    // the type of error if any
    this.error = error || null;
};

JRPC.Response.prototype.data = function() {
    return {
        id: this.id,
        result: this.result,
        error: this.error,
    };
};

JRPC.Response.prototype.json = function() {
    return JSON.stringify(this.data());
};

// JRPC.WebSocket
// The main object for interacting with a remote
// JRPC peer. It support calling remote methods
// and serving remote requests. A dispatch object
// is used to define a mapping of RPC method names
// to function callables.
JRPC.WebSocket = function(host, port, dispatch, callback) {
    // generate the websocket endpoint uri
    var endpoint = make_endpoint(host, port);
    // create the underlying websocket
    this.socket = new WebSocket(endpoint);
    this.socket.binaryType = "arraybuffer";
    // the method handler mapping
    this.dispatch = dispatch;
    // a record of pending remote requests
    this.requests = {};
    // the next request id
    this._rid = 0;
    // connected callback
    this._callback = callback

    // Event Listeners
    // WebSocket event listeners will be called in the context
    // of the WebSocket itself. Each event listener is set to
    // a small wrapper function that calls the corresponding
    // method on this JRPC.WebSocket instance.
    var rpc_socket = this; // save value of this in current closure
    this.socket['onclose'] = function(e) { rpc_socket.onClose(e) };
    this.socket['onerror'] = function(e) { rpc_socket.onError(e) };
    this.socket['onmessage'] = function(e) { rpc_socket.onMessage(e) };
    this.socket['onopen'] = function(e) { rpc_socket.onOpen(e) };
};

JRPC.WebSocket.prototype.onOpen = function(e) {
    // The websocket connection has been established
    console.log("Connection established to: " + this.socket.url);
    if (this._callback) {
        this._callback();
    }
};

JRPC.WebSocket.prototype.onClose = function(e) {
    // The websocket has been closed
    console.log("Connection closed to: " + this.socket.url);
    console.log(e);
};

JRPC.WebSocket.prototype.onError = function(e) {
    // An error related to the websocket occured
    console.log("Error in connection to: " + this.socket.url);
    console.log(e);
};

JRPC.WebSocket.prototype.onMessage = function(e) {
    // A message was received over the websocket
    this.handle(e)
};

// JRPC.WebSocket.invoke
// Call a remote method but do not expect a result
JRPC.WebSocket.prototype.invoke = function(method, args, kwargs) {
    var request = new JRPC.Request(method, args, kwargs);
    this.socket.send(request.json());
};

// JRPC.WebSocket.request
// Call a remote method and register a callback and/or
// a errback for when the result has been recieved.
JRPC.WebSocket.prototype.request = function(method, args, kwargs, cb, eb) {
    var request = new JRPC.Request(method, args, kwargs, this._rid);
    this.requests[this._rid] = {cb: cb, eb: eb};
    this._rid += 1;
    this.socket.send(request.json());
};

// JRPC.WebSocket.handle_response
// Handle an incomming response from a previously made
// request to call a remote method. The result is may
// potentially be an error in which the registered
// error handler will be called if any.
JRPC.WebSocket.prototype.handle_response = function(object) {
    // generate the response object
    var response = new JRPC.Response(object.id,
                                    object.result,
                                    object.error);
    // obtain the registered handlers for this id
    var handlers = this.requests[response.id];
    // unregister the handlers
    delete this.requests[response.id];
    // call the appropriate callback depending on whether
    // an error type was provided.
    if (response.error != null) {
        if (handlers.eb) {
            handlers.eb(response);
        } else {
            console.log("Unhandled error response: " + response.error + " " + response.result);
        }
    } else {
        handlers.cb(response);
    }
};

// JRPC.WebSocket.handle_request
// Handle an incomming request to call a local method.
// If the request contains an id return a result to
// the caller.
JRPC.WebSocket.prototype.handle_request = function(object) {
    // generate the new request object from the remote message
    var request = new JRPC.Request(object.method,
                                  object.args,
                                  object.kwargs,
                                  object.id)
    // obtain the handler registered for this method
    var handler = this.dispatch[request.method];
    // call the handler and obtain the result
    var result = handler(request.args, request.kwargs);
    // if the request provided a tracking id return the
    // result to the caller
    if (request.id) {
        var response = new JRPC.Response(request.id, result, null);
        this.socket.send(response.json());
    }
};

// JRPC.WebSocket.handle
// Handle an incomming message from the remote peer.
// Messages may either be remote requests for local
// method invocation or the result of our own request.
JRPC.WebSocket.prototype.handle = function(payload) {
    var obj = JSON.parse(payload.data);
    if (obj.hasOwnProperty('result')) {
        this.handle_response(obj);
    } else {
        this.handle_request(obj);
    }
}

return JRPC;

}();
