var Container = React.createClass({
    onClick: function() {
        cpContainers.setAttached(this.props.data.Id);
    },
    render: function() {
        var data = this.props.data;
        var selected = this.props.selected;
        var selectionClass = this.props.isSelected ? "selected container" : "container";
        return (
            <tr className={selectionClass}
                onClick={this.onClick}
                id={data.Id}>
                <td>{data.Id.substring(0, 7)}</td>
                <td>{data.Image}</td>
                <td>{data.Command}</td>
                <td>{data.Status}</td>
            </tr>
        );
    },
});

var ContainerTable = React.createClass({
    getInitialState: function() {
        return {
            containers: [],
            attached: null,
        };
    },
    setAttached: function(id) {
        console.log("Attaching to: " + id);
        var cid = null;
        for(var i=0; i<this.state.containers.length; i++) {
            var container = this.state.containers[i];
            if (container.Id == id) {
                cid = id;
            }
        }
        this.setState({attached: cid});
        rpc.invoke('Attach', [cid]);
        cpTerminal.clear();
    },
    setContainers: function(containers) {
        cpTerminal.clear();
        this.setState({'containers': containers});
        this.setAttached(this.state.attached);
    },
    generateContainer: function(container) {
        return (
            <Container data={container}
                       isSelected={this.state.attached==container.Id} />
        );
    },
    render: function() {
        var containers = this.state.containers;
        return (
            <table>
                <thead>
                    <tr>
                        <td>ID</td>
                        <td>Image</td>
                        <td id="cmd">Cmd</td>
                        <td>Status</td>
                    </tr>
                </thead>
                <tbody>
                    {containers.map(this.generateContainer, this)}
                </tbody>
            </table>
        );
    }
});

var cpContainers = React.render(
  <ContainerTable />,
  document.getElementById('containers')
);
