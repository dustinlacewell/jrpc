var WS_HOST = window.location.hostname;
var WS_PORT = 9000

var rpc = null;

(function(){
    rpc = new JRPC.WebSocket(WS_HOST, WS_PORT, {}, function() {
        rpc.request('Echo', ["Hello World"], {}, function(r) {
            alert(r.result);
        });
    });
})();
