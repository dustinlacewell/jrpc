var TerminalLog = React.createClass({
    getInitialState: function() {
        return {terminal: null};
    },
    render: function() {
        return (
            <div id="console"></div>
        );
    },
    componentDidMount: function() {
        var terminal_element = React.findDOMNode(this);
        var $terminal = $(terminal_element);
        $terminal.height($(window).height() * .98);
        var terminal = $terminal.jqconsole('', '');
        this.setState({terminal: terminal});
        terminal.Write("JQConsole loaded.\n");
    },
    write: function(msg) {
        this.state.terminal.Write(msg);
    },
    writeln: function(msg) {
        this.write(msg + "\n");
    },
    clear: function() {
        this.state.terminal.Clear();
    },
});

var cpTerminal = React.render(
    <TerminalLog />,
    document.getElementById('logs')
);
