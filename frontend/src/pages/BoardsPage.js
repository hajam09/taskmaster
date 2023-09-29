import React, {Component} from "react";
import SingleAvatarEntityComponent from "../components/SingleAvatarEntityComponent";
import MultipleAvatarEntityComponent from "../components/MultipleAvatarEntityComponent";

class BoardTypeComponent extends Component {
    constructor(props) {
        super(props);
    }

    renderKanbanBadge = () => {
        return (
            <span className="badge" style={{color: "white", backgroundColor: "#7f45dd"}}>
                KANBAN
            </span>
        )
    }

    renderScrumBadge = () => {
        return (
            <span className="badge" style={{color: "white", backgroundColor: "#00761b"}}>
                SCRUM
            </span>
        )
    }

    render() {
        return (
            <div>
                {this.props.type.toLowerCase() === "kanban" ? this.renderKanbanBadge() : this.renderScrumBadge()}
            </div>
        )
    }
}

class BoardVisibilityComponent extends Component {
    constructor(props) {
        super(props);
    }

    renderPrivateBadge = () => {
        return (
            <span className="badge" style={{color: "#bf2600", backgroundColor: "#ffebe6"}}>
                Restricted
            </span>
        )
    }

    renderPublicBadge = () => {
        return (
            <span className="badge" style={{color: "#403294", backgroundColor: "#eae6ff"}}>
                All Users
            </span>
        )
    }

    render() {
        return (
            <div>
                {this.props.isPrivate ? this.renderPrivateBadge() : this.renderPublicBadge()}
            </div>
        )
    }
}

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
            admins: newAdmins,
            members: newMembers,
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

    renderProjectIcons = () => {
        if (this.props.data.projects.length === 1) {
            return (
                <SingleAvatarEntityComponent key={this.props.data.projects[0].id}
                                             internalKey={this.props.data.projects[0].internalKey}
                                             icon={this.props.data.projects[0].icon}
                                             href={`/issuesListView/?project=${this.props.data.projects[0].internalKey}`}/>
            )
        } else {
            return (
                <ul className="avatars">
                    {this.props.data.projects.map((project) => <MultipleAvatarEntityComponent key={project.id}
                                                                                              internalKey={project.internalKey}
                                                                                              icon={project.icon}
                                                                                              href={`/issuesListView/?project=${project.internalKey}`}/>)}
                </ul>
            )
        }
    }

    render() {
        return (
            <tr>
                <td>
                    <a href={`/boards/${this.props.data.url}/`}>{this.props.data.internalKey}</a>
                </td>
                <td>
                    {this.renderAdminIcons()}
                </td>
                <td>
                    {this.renderMemberIcons()}
                </td>
                <td>
                    <BoardTypeComponent type={this.props.data.type}/>
                </td>
                <td>
                    <BoardVisibilityComponent isPrivate={this.props.data.isPrivate}/>
                </td>
                <td>
                    {this.renderProjectIcons()}
                </td>
            </tr>
        )
    }
}

export default class BoardsPage extends Component {
    constructor(props) {
        super(props);

        this.state = {
            boards: [],
            openModal: false,
        }
    }

    componentDidMount = () => {
        fetch("/api/v1/boards", {
            method: 'GET',
        }).then((response) => response.json())
            .then((json) => {
                this.setState({
                    boards: json
                })

                $("#boardTable").DataTable(
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

    renderNoBoardComponent = () => {
        return (
            <div className="alert alert-primary text-center" role="alert">
                Looks like there's no board to see. Create one.
            </div>
        )
    }

    renderBoardListComponent = () => {
        return (
            <table id="boardTable" className="table table-sm table-bordered table-hover">
                <thead>
                <tr>
                    <th>Name</th>
                    <th>Admins</th>
                    <th>Members</th>
                    <th>Type</th>
                    <th>Visibility</th>
                    <th>Project</th>
                </tr>
                </thead>
                <tbody>
                {this.state.boards.map((entry) => <TableEntryComponent key={entry.id} data={entry}/>)}
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
                                <h3>Boards</h3>
                            </div>
                            <div className="col">
                                <button type="button" className="btn btn-primary float-right" disabled={true}>Create
                                    board
                                </button>
                            </div>
                        </div>
                        <br></br>
                        {this.state.boards.length === 0 ? this.renderNoBoardComponent() : this.renderBoardListComponent()}
                    </div>
                </div>
            </div>
        );
    }
}