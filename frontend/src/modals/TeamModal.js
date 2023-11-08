import React, {Component} from "react";
import {TextField} from "@material-ui/core";




export default class TeamModal extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div className="modal fade bd-example-modal-lg" id="newTeamModal" tabIndex="-1" role="dialog"
                 aria-hidden="true" style={{color: "black"}}>
                <div className="modal-dialog" role="document">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title" id="exampleModalLabel">Create teams</h5>
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="tab-content">
                                <dl className="row">
                                    <dd className="col-md-12">
                                        <TextField id="name" label="Name" variant="outlined" size="small" fullWidth/>
                                    </dd>
                                    <dd className="col-md-12">
                                        <TextField variant="outlined" label="Description" id="description" multiline
                                                   fullWidth minRows={5}/>
                                    </dd>
                                </dl>
                                <br></br>
                                <div className="alert alert-warning alert-dismissible fade show" role="alert">
                                    You can edit these details at any time.
                                    <button type="button" className="close" data-dismiss="alert"
                                            aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <input className="btn btn-primary" type="submit" value="Create Team"></input>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}