import React, {Component} from "react";
import SingleAvatarEntityComponent from "../components/SingleAvatarEntityComponent";
import MultipleAvatarEntityComponent from "../components/MultipleAvatarEntityComponent";
import TeamModal from "../modals/TeamModal";


class TableEntryComponent extends Component {

    constructor(props) {
        super(props);

        let newAdmins = [];
        let newMembers = [];

        for (const admin of this.props.data.admins) {
            let adminClone = structuredClone(admin);
            adminClone.internalKey = adminClone.first_name + " " + adminClone.last_name;
            newAdmins.push(adminClone)
        }

        for (const member of this.props.data.members) {
            let memberClone = structuredClone(member);
            memberClone.internalKey = memberClone.first_name + " " + memberClone.last_name;
            newMembers.push(memberClone)
        }

        this.state = {
            admins: newAdmins, members: newMembers,
        }
    }

    renderAdminIcons = () => {
        if (this.state.admins.length === 1) {
            return (
                <SingleAvatarEntityComponent key={this.state.admins[0].id}
                                             internalKey={this.state.admins[0].internalKey}
                                             icon={this.state.admins[0].icon}
                                             href={null}/>
            )
        } else {
            return (
                <ul className="avatars">
                    {this.state.admins.map((admin) => <MultipleAvatarEntityComponent key={admin.id}
                                                                                     internalKey={admin.internalKey}
                                                                                     icon={admin.icon}
                                                                                     href={null}/>)}
                </ul>
            )
        }
    }

    renderMemberIcons = () => {
        if (this.state.members.length === 1) {
            return (
                <SingleAvatarEntityComponent key={this.state.members[0].id}
                                             internalKey={this.state.members[0].internalKey}
                                             icon={this.state.members[0].icon}
                                             href={null}/>
            )
        } else {
            return (
                <ul className="avatars">
                    {this.state.members.map((member) => <MultipleAvatarEntityComponent key={member.id}
                                                                                       internalKey={member.internalKey}
                                                                                       icon={member.icon}
                                                                                       href={null}/>)}
                </ul>
            )
        }
    }

    render() {
        return (<tr>
            <td>
                <a href={`/teams/${this.props.data.url}/`}>{this.props.data.internalKey}</a>
            </td>
            <td>
                {this.renderAdminIcons()}
            </td>
            <td>
                {this.renderMemberIcons()}
            </td>
        </tr>)
    }
}

export default class TeamsPage extends Component {
    constructor(props) {
        super(props);

        this.state = {
            teams: []
        }
    }

    componentDidMount = () => {
        fetch("/api/v1/teams", {
            method: 'GET',
        }).then((response) => response.json())
            .then((json) => {
                this.setState({
                    teams: json
                })

                $("#teamsTable").DataTable({
                    "responsive": true,
                    "autoWidth": false,
                    "paging": true,
                    "searching": true,
                    "ordering": true,
                    "info": false,
                    "pageLength": 10,
                });
            })
    }

    renderNoTeamsComponent = () => {
        return (
            <div className="alert alert-primary text-center" role="alert">
                Looks like there's no team to see. Create one.
            </div>
        )
    }

    renderTeamsListComponent = () => {
        return (
            <table id="teamsTable" className="table table-sm table-bordered table-hover">
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Admins</th>
                    <th>Members</th>
                </tr>
                </thead>
                <tbody>
                {this.state.teams.map((entry) => <TableEntryComponent key={entry.id} data={entry}/>)}
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
                                <h3>Teams</h3>
                            </div>
                            <div className="col">
                                <button type="button" className="btn btn-primary float-right" data-toggle="modal"
                                        data-target="#newTeamModal" disabled={true}>Create
                                    Team
                                </button>
                                <TeamModal/>
                            </div>
                        </div>
                        <br></br>
                        {this.state.teams.length === 0 ? this.renderNoTeamsComponent() : this.renderTeamsListComponent()}
                    </div>
                </div>
            </div>
        );
    }
}