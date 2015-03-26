var WS_HOST = window.location.hostname;
var WS_PORT = 9000

var rpc = null;

var doRefresh = function(args, kwargs) {
    var containers = kwargs.containers;
    cpContainers.setState({'containers': containers});
}

var doLog = function(args, kwargs) {
    cpTerminal.writeln(kwargs.message);
}

$(document).ready(function(){
    rpc = new JRPC.WebSocket(WS_HOST, WS_PORT, {
        'Refresh': doRefresh,
        'Log': doLog,
    });
});
