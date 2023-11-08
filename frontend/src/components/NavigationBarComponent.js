import React, {Component} from "react";

export default class NavigationBarComponent extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
                <a className="navbar-brand" href="#">TaskMaster</a>
                <button type="button" className="btn btn-primary float-left pull-left">Create</button>
                <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNavDropdown"
                        aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
                    <span className="navbar-toggler-icon"></span>
                </button>
                <div className="collapse navbar-collapse" id="navbarNavDropdown">
                    <ul className="navbar-nav ml-auto">
                        <li className="nav-item active">
                            <a className="nav-link" href="" data-toggle="tooltip" data-placement="right"
                               title="Home"> Home </a>
                        </li>
                        <li className="nav-item dropdown">
                            <a className="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button"
                               data-toggle="dropdown" aria-haspopup="true" aria-expanded="true"> Account </a>
                            <div className="dropdown-menu dropdown-menu-right" aria-labelledby="navbarDropdown">
                                <a className="dropdown-item" href="/dashboard/">
                                    <i style={{fontSize: "15px"}} className="fas fa-chalkboard"></i> Dashboard </a>
                                <a className="dropdown-item" href="/teams/">
                                    <i style={{fontSize: "15px"}} className="fa fa-users"></i> Teams </a>
                                <a className="dropdown-item" href="/projects/">
                                    <i style={{fontSize: "15px"}} className="fas fa-project-diagram"></i> Projects </a>
                                <a className="dropdown-item" href="/boards/">
                                    <i style={{fontSize: "15px"}} className="far"></i> Boards </a>
                                <a className="dropdown-item" href="/accounts/account-settings?tab=profileAndVisibility">
                                    <i style={{fontSize: "15px"}} className="fa"></i> Settings </a>
                                <div className="dropdown-divider"></div>
                                <a className="dropdown-item" href="/accounts/logout/">
                                    <i style={{fontSize: "15px"}} className="fas fa-sign-out-alt"></i> Logout </a>
                            </div>
                        </li>
                    </ul>
                </div>
            </nav>
        );
    }
}