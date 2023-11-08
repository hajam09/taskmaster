import React, {Component} from "react";
import SingleAvatarEntityComponent from "../components/SingleAvatarEntityComponent";
class TableEntryComponent extends Component {
    constructor(props) {
        super(props);

        let leadClone = structuredClone(this.props.data.lead);
        leadClone.internalKey = leadClone.first_name + " " + leadClone.last_name;

        this.state = {
            leads: leadClone,
        }
    }

    render() {
        return (
            <tr>
                <td>
                    {/*<SingleAvatarEntityComponent icon={this.props.data.icon} internalKey={this.props.data.internalKey} href={null}/>*/}
                </td>
                <td>{this.props.data.code}</td>
                <td>

                </td>
                <td>
                    <span className={this.props.data.status.icon}
                          style={{textTransform: "uppercase"}}>{this.props.data.status.internalKey}</span>
                </td>
                <td>
                    <a role="button" href={"/projects/" + this.props.data.url + "/settings"}
                       className="btn btn-outline-secondary" data-toggle="tooltip"
                       data-placement="top" title="Settings"><SettingsIcon/>
                    </a>
                </td>
            </tr>
        )
    }
}

export default class ProjectsPage extends Component {
    constructor(props) {
        super(props);

        this.state = {
            projects: [],
        }
    }

    componentDidMount = () => {
        fetch("/api/v1/projects", {
            method: 'GET',
        }).then((response) => response.json())
            .then((json) => {
                this.setState({
                    projects: json
                })

                $("#projectsTable").DataTable(
                    {
                        "responsive": true,
                        "autoWidth": false,
                        "paging": true,
                        "searching": true,
                        "ordering": true,
                        "info": false,
                        "pageLength": 10,
                    }
                );
            })
    }

    renderNoProjectComponent = () => {
        return (
            <div className="alert alert-primary text-center" role="alert">
                Looks like there's no project to see. Create one.
            </div>
        )
    }

    renderProjectListComponent = () => {
        return (
            <table id="projectsTable" className="table table-sm table-bordered table-hover">
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Key</th>
                    <th>Lead</th>
                    <th>Status</th>
                    <th>Links</th>
                </tr>
                </thead>
                <tbody>
                {this.state.projects.map((entry) => <TableEntryComponent key={entry.id} data={entry}/>)}
                </tbody>
            </table>
        )
    }

    render() {
        return (
            <div className="container-fluid" style={{margin: "auto", color: "black", maxWidth: "1800px"}}>
                <br></br>
                <div className="row">
                    <div className="col-12">
                        <div className="row">
                            <div className="col">
                                <h3>Projects</h3>
                            </div>
                            <div className="col">
                                <button type="button" className="btn btn-primary float-right">Create Project</button>
                            </div>
                        </div>
                        <br></br>
                        {this.state.projects.length === 0 ? this.renderNoProjectComponent() : this.renderProjectListComponent()}
                    </div>
                </div>
            </div>
        );
    }
}