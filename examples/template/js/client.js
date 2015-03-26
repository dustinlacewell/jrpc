var WS_HOST = window.location.hostname;
var WS_PORT = 9000

var rpc = null;

var doAlert = function(args, kwargs) {
    alert(kwargs.message);
};

(function(){
    rpc = new JRPC.WebSocket(WS_HOST, WS_PORT, {
        'Alert': doAlert,
    }, function() {
        rpc.invoke('Add', [5, 10]);
    });
})();
