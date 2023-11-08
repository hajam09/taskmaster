import React, {Component} from "react";


class TicketBar extends Component {
    constructor(props) {
        super(props);
    }

    renderProfile = () => {
        if (this.props.ticket.assignee === null || true) {
            return (
                <img src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                     className="ghx-avatar-img"
                     data-toggle="tooltip"
                     data-placement="top"
                     title="Unassigned"
                     loading="lazy"></img>
            );
        } else {
            return (
                <img src={this.props.ticket.asignee}
                     className="ghx-avatar-img"
                     data-toggle="tooltip"
                     data-placement="top"
                     title={this.props.ticket.assignee.first_name + " " + this.props.ticket.assignee.last_name}
                     loading="lazy"></img>
            );
        }
    }

    render() {
        return (
            <div className="card" id={this.props.ticket.id}>
                <div className="card-body" style={{height: "10px"}}>
                    <div className="row" style={{marginTop: "-13px"}}>
                        <div className="col-auto" style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                            <img src={this.props.ticket.issueType.icon} width="20" height="20" data-toggle="tooltip"
                                 data-placement="top" title={this.props.ticket.issueType.internalKey}></img>
                        </div>
                        <div className="col-auto" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                            <a href={`/jira/ticket/${this.props.ticket.internalKey}/`}>{this.props.ticket.internalKey}</a>
                        </div>
                        <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                            <span>{this.props.ticket.summary}</span>
                        </div>
                        <div className="col-auto" style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                            <img src={this.props.ticket.priority.icon} width="20" height="20" data-toggle="tooltip"
                                 data-placement="top" title={this.props.ticket.priority.internalKey}></img>
                        </div>
                        <div className="col-auto" style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                            <span className="badge badge-pill badge-secondary">
                                {this.props.ticket.storyPoints === null ? "-" : this.props.ticket.storyPoints}
                            </span>
                        </div>
                        <div className="col-auto" style={{marginTop: "-15px;", marginLeft: "-25px"}}>
                            {this.renderProfile()}
                        </div>
                    </div>
                </div>
            </div>
        )
    }
}

class TeamMembersComponent extends Component {
    constructor(props) {
        super(props);

        let adminsAndMembers = this.props.admins.concat(this.props.members);
        const uniquePeople = adminsAndMembers.reduce((acc, current) => {
            const x = acc.find(item => item.id === current.id);
            return !x ? acc.concat([current]) : acc;
        }, []);

        this.state = {
            members: uniquePeople,
        }
    }

    render() {
        return (
            <div>
                <div className="card card-header">
                    <b>Team members</b>
                    <small>{this.state.members.length} member(s)</small>
                </div>
                <div className="card card-body">

                    {this.state.members.map((member) => <span key={member.id}>

                        <div className="row">
                            <div className="col-2">

                                <img alt={`${member.first_name} ${member.last_name}`} className="avatar filter-by-alt"
                                    src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                    data-filter-by="alt"></img>

                            </div>
                            <div className="col-10">{`${member.first_name} ${member.last_name}`}
                                <br></br>
                                <small className="text-secondary">{member.jobTitle}</small>
                            </div>
                        </div>
                        <div style={{height: "15px"}}></div>
                    </span>
                    )}
                </div>
            </div>
        );
    }
}

export default class TeamsPage extends Component {
    constructor(props) {
        super(props);

        this.state = {
            team: null,
            teamTickets: [],
        }
    }

    componentDidMount = () => {
        fetch(`/api/v1/team-view/${this.props.match.params.url}`, {
            method: 'GET',
        }).then((response) => response.json())
            .then((json) => {
                this.setState({
                    team: json.team,
                    teamTickets: json.teamTickets,
                })
            })
    }

    renderTeam = () => {
        return(
            <div className="container-fluid"
                     style={{margin: "auto", overflowX: "hidden", color: "black", maxWidth: "1500px"}}>
                    <div className="gutters-sm">
                        <div style={{height: "30px"}}></div>
                        <div className="col-md-12">
                            <div className="row">
                                <div className="col-md-4">
                                    <h4>Team - C6-6002540v</h4>


                                    <p className="text-secondary">&nbsp;<i
                                        className="fas fa-unlock"></i>&nbsp;&nbsp;Open team</p>


                                    <div style={{height: "10px"}}></div>


                                    <p className="text-secondary">&nbsp;{this.state.team.description}</p>

                                    <button type="button" className="btn btn-light"
                                            style={{background: "#f5f6f8", width: "83%"}} data-toggle="modal"
                                            data-target="#addPeopleModal">Add
                                        people
                                    </button>
                                    &nbsp;
                                    <button role="button" type="button" className="btn dropdown" data-toggle="dropdown"
                                            style={{background: "#f5f6f8", width: "15%"}}>
                                        <i className="fa fa-ellipsis-h"></i>
                                    </button>
                                    <div className="dropdown-menu" aria-labelledby="dropdownMenuButton">
                                        <span className="dropdown-item" onClick="leaveTeam();">Leave team</span>
                                        <span className="dropdown-item" onClick="deleteTeam();">Delete team</span>
                                    </div>

                                    <div style={{height: "30px"}}></div>

                                    {
                                        <TeamMembersComponent admins={this.state.team.admins} members={this.state.team.members}/>
                                    }


                                </div>
                                <div className="col-md-1"></div>
                                <div className="col-md-7" id="div-id-forum-list-container">
                                    <h5>Team activity</h5>
                                    <div className="card">

                                        {this.state.teamTickets.map((ticket) => <TicketBar key={ticket.id}
                                                                                           ticket={ticket}/>)}

                                    </div>
                                    <div style={{height: "30px"}}></div>

                                    <h5>Team chat</h5>

                                    <div className="alert alert-danger" role="alert">
                                        Unfortunately you do not have the permission to view this team chat. If this is
                                        a
                                        mistake then please contact this teams administrators!
                                    </div>

                                </div>
                            </div>
                        </div>
                    </div>
                </div>
        )
    }

    render() {
        return (
            <div>
                <div>
                    <div className="p-3 mb-2 text-white bg-secondary" style={{height: "180px"}}>
                        <div className="container" style={{paddingTop: "110px"}}>
                        </div>
                    </div>
                </div>
                {this.state.team !== null ? this.renderTeam() : null}
            </div>
        )
    }
}