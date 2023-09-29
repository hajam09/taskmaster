import React, {Component} from "react";
export default class TeamsPage extends Component {
    constructor(props) {
        super(props);

        console.log(this.props.match.params.url)

        this.state = {
            team: null,
        }
    }

    componentDidMount = () => {
        fetch(`/api/v1/teams/${this.props.match.params.url}`, {
            method: 'GET',
        }).then((response) => response.json())
            .then((json) => {
                this.setState({
                    team: json
                })
            })
    }

    render() {
        return (
            <div>
                <div>
                    <div className="p-3 mb-2 text-white bg-secondary" style={{height:"180px"}}>
                        <div className="container" style={{paddingTop: "110px"}}>
                        </div>
                    </div>
                </div>
                <div className="container-fluid"
                     style={{margin: "auto", overflowX: "hidden", color: "black", maxWidth: "1500px"}}>
                    <div className="gutters-sm">
                        <div style={{height:"30px"}}></div>
                        <div className="col-md-12">
                            <div className="row">
                                <div className="col-md-4">
                                    <h4>Team - C6-6002540v</h4>


                                    <p className="text-secondary">&nbsp;<i
                                        className="fas fa-unlock"></i>&nbsp;&nbsp;Open team</p>


                                    <div style={{height:"10px"}}></div>


                                    <p className="text-secondary">&nbsp;Benjamin Humphrey DVM</p>

                                    <button type="button" className="btn btn-light"
                                            style={{background: "#f5f6f8", width: "83%"}} data-toggle="modal"
                                            data-target="#addPeopleModal">Add
                                        people
                                    </button>
                                    <button role="button" type="button" className="btn dropdown" data-toggle="dropdown"
                                            style={{background: "#f5f6f8", width: "15%"}}>
                                        <i className="fa fa-ellipsis-h"></i>
                                    </button>
                                    <div className="dropdown-menu" aria-labelledby="dropdownMenuButton">
                                        <span className="dropdown-item" onClick="leaveTeam();">Leave team</span>
                                        <span className="dropdown-item" onClick="deleteTeam();">Delete team</span>
                                    </div>

                                    <div style={{height:"30px"}}></div>


                                    <div className="card card-header">
                                        <b>Team members</b>
                                        <small>5 members</small>
                                    </div>
                                    <div className="card card-body">

                                        <div className="row">
                                            <div className="col-2">

                                                <img alt="James Cooke" className="avatar filter-by-alt"
                                                     src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                                     data-filter-by="alt"></img>

                                            </div>
                                            <div className="col-10">
                                                James Cooke<br></br><small className="text-secondary">Project Owner</small>
                                            </div>
                                        </div>
                                        <div style={{height:"15px"}}></div>

                                        <div className="row">
                                            <div className="col-2">

                                                <img alt="Paul Snow" className="avatar filter-by-alt"
                                                     src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                                     data-filter-by="alt"></img>

                                            </div>
                                            <div className="col-10">
                                                Paul Snow<br></br><small className="text-secondary">Solutions
                                                Architect</small>
                                            </div>
                                        </div>
                                        <div style={{height:"15px"}}></div>

                                        <div className="row">
                                            <div className="col-2">

                                                <img alt="Caitlin Mccullough" className="avatar filter-by-alt"
                                                     src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                                     data-filter-by="alt"></img>

                                            </div>
                                            <div className="col-10">
                                                Caitlin Mccullough<br></br><small className="text-secondary">Project
                                                Manager</small>
                                            </div>
                                        </div>
                                        <div style={{height:"15px"}}></div>

                                        <div className="row">
                                            <div className="col-2">

                                                <img alt="Anthony Mccoy" className="avatar filter-by-alt"
                                                     src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                                     data-filter-by="alt"></img>

                                            </div>
                                            <div className="col-10">
                                                Anthony Mccoy<br></br><small className="text-secondary">Project
                                                Manager</small>
                                            </div>
                                        </div>
                                        <div style={{height:"15px"}}></div>

                                        <div className="row">
                                            <div className="col-2">

                                                <img alt="Michael Taylor" className="avatar filter-by-alt"
                                                     src="https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png"
                                                     data-filter-by="alt"></img>

                                            </div>
                                            <div className="col-10">
                                                Michael Taylor<br></br><small className="text-secondary">Solutions
                                                Architect</small>
                                            </div>
                                        </div>
                                        <div style={{height:"15px"}}></div>

                                    </div>
                                </div>
                                <div className="col-md-1"></div>
                                <div className="col-md-7" id="div-id-forum-list-container">
                                    <h5>Team activity</h5>
                                    <div className="card">

                                        <div className="card" id="1543">
                                            <div className="card-body" style={{height: "10px"}}>
                                                <div className="row" style={{marginTop: "-13px"}}>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/cc/5e/08/ME14ZPM6_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Story/"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <a href="/jira/ticket/OWKFOWXW-1542/">OWKFOWXW-1542</a>
                                                    </div>
                                                    <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <span>X0-3836652n</span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/17/d5/e6/ME14ZPLK_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Medium"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                                                    <span className="badge badge-pill badge-secondary">

                                                            -

                                                    </span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-15px;", marginLeft: "-25px"}}>

                                                        <img src="/media/avatars/panda.png" className="ghx-avatar-img"
                                                             data-toggle="tooltip" data-placement="top" title="James"
                                                             cooke="" loading="lazy"></img>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="card" id="1544">
                                            <div className="card-body" style={{height: "10px"}}>
                                                <div className="row" style={{marginTop: "-13px"}}>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/9c/bb/4c/ME14ZPM8_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Sub" task=""></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <a href="/jira/ticket/OWKFOWXW-1543/">OWKFOWXW-1543</a>
                                                    </div>
                                                    <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <span>y0-810851X</span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/17/d5/e6/ME14ZPLK_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Medium"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                                                    <span className="badge badge-pill badge-secondary">

                                                            -

                                                    </span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-15px;", marginLeft: "-25px"}}>

                                                        <img src="/media/avatars/panda.png" className="ghx-avatar-img"
                                                             data-toggle="tooltip" data-placement="top" title="James"
                                                             cooke="" loading="lazy"></img>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="card" id="1545">
                                            <div className="card-body" style={{height: "10px"}}>
                                               <div className="row" style={{marginTop: "-13px"}}>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/12/1c/8d/ME14ZPM2_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Improvement/"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <a href="/jira/ticket/BTSCWPTZ-1544/">BTSCWPTZ-1544</a>
                                                    </div>
                                                    <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <span>v1-7531110t</span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/17/d5/e6/ME14ZPLK_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Medium"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                                                    <span className="badge badge-pill badge-secondary">

                                                            -

                                                    </span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-15px;", marginLeft: "-25px"}}>

                                                        <img src="/media/avatars/panda.png" className="ghx-avatar-img"
                                                             data-toggle="tooltip" data-placement="top" title="James"
                                                             cooke="" loading="lazy"></img>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="card" id="1546">
                                            <div className="card-body" style={{height: "10px"}}>
                                                <div className="row" style={{marginTop: "-13px"}}>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/d1/5c/cd/ME14ZPM9_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Task/"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <a href="/jira/ticket/OWKFOWXW-1545/">OWKFOWXW-1545</a>
                                                    </div>
                                                    <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <span>C2-682469s</span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/17/d5/e6/ME14ZPLK_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Medium"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                                                    <span className="badge badge-pill badge-secondary">

                                                            -

                                                    </span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-15px;", marginLeft: "-25px"}}>

                                                        <img src="/media/avatars/panda.png" className="ghx-avatar-img"
                                                             data-toggle="tooltip" data-placement="top" title="James"
                                                             cooke="" loading="lazy"></img>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="card" id="1549">
                                            <div className="card-body" style={{height: "10px"}}>
                                                <div className="row" style={{marginTop: "-13px"}}>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-10px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/90/63/63/ME14ZPM4_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Spike/"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <a href="/jira/ticket/BTSCWPTZ-1548/">BTSCWPTZ-1548</a>
                                                    </div>
                                                    <div className="col" style={{marginTop: "-11px;", marginLeft: "-13px"}}>
                                                        <span>N1-3043799R</span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-13px;", marginLeft: "-13px"}}>
                                                        <img
                                                            src="https://cdn-thumbs.imagevenue.com/17/d5/e6/ME14ZPLK_t.jpg"
                                                            width="20" height="20" data-toggle="tooltip"
                                                            data-placement="top" title="Medium"></img>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-12px;", marginLeft: "-25px"}}>
                                                    <span className="badge badge-pill badge-secondary">

                                                            -

                                                    </span>
                                                    </div>
                                                    <div className="col-auto"
                                                         style={{marginTop: "-15px;", marginLeft: "-25px"}}>

                                                        <img src="/media/avatars/panda.png" className="ghx-avatar-img"
                                                             data-toggle="tooltip" data-placement="top" title="James"
                                                             cooke="" loading="lazy"></img>

                                                    </div>
                                                </div>
                                            </div>
                                        </div>

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
            </div>
        )
    }
}