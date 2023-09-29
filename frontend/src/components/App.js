import React, {Component} from "react";
import {render} from "react-dom";
import NavigationBarComponent from "./NavigationBarComponent";
import {Grid, Button, ButtonGroup, Typography} from "@material-ui/core";
import {
    BrowserRouter as Router,
    Switch,
    Route,
    Link,
    Redirect,
} from "react-router-dom";
import TeamsPage from "../pages/TeamsPage";
import BoardsPage from "../pages/BoardsPage";
import ProjectsPage from "../pages/ProjectsPage";
import TeamPage from "../pages/TeamPage";

export default class App extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <span>
                <NavigationBarComponent/>
                <div className="container-fluid">
                <Router>
                <Switch>
                    <Route path="/teams/:url/" component={TeamPage}/>
                    <Route path="/teams" component={TeamsPage}/>
                    <Route path="/boards" component={BoardsPage}/>
                    <Route path="/projects" component={ProjectsPage}/>

                </Switch>
            </Router>
            </div>
            </span>

        );
    }
}

const appDiv = document.getElementById("app");
render(<App/>, appDiv);