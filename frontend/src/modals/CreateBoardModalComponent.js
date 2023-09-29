import React, {Component} from "react";

import {FormControl, FormControlLabel, FormLabel, Radio, RadioGroup, TextField} from "@material-ui/core";
import {Alert} from "@material-ui/lab";


export default class CreateBoardModalComponent extends Component {
    constructor(props) {
        super(props);
        // TODO: NOT DONE
    }

    componentDidMount = () => {
        $('.select2bs4').select2();
    }

    render() {
        return (
            <div className="modal fade bd-example-modal-lg" id="newBoardModal" tabIndex="-1" role="dialog"
                 aria-labelledby="myLargeModalLabel" aria-hidden="true" style={{color: "black"}}>
                <div className="modal-dialog" role="document">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title" id="exampleModalLabel">Create Board</h5>
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>

                        <div className="modal-body">
                            <dl className="row">
                                <dd className="col-sm-12">
                                    <TextField id="boardName" fullWidth label="Name" variant="standard"/>
                                </dd>

                            </dl>

                            <Alert severity="info">You can edit these details at any time.</Alert>
                            <br></br>
                            <Alert severity="info">NOTE: The board may appear to other users. But don't worry, they
                                won't be able to
                                access it.</Alert>

                        </div>
                    </div>
                </div>
            </div>
        )
    }
}