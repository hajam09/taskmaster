import React, {Component} from "react";

export default class SingleAvatarEntityComponent extends Component {
    constructor(props) {
        super(props);

        this.state = {
            icon: this.props.icon === null ? "https://cdn3.iconfinder.com/data/icons/avatars-round-flat/33/man5-512.png" : this.props.icon,
            internalKey: this.props.internalKey,
            href: this.props.href === null || this.props.href === undefined ? "#" : this.props.href,
        }
    }

    render() {
        return (
            <span className="row">
                <span className="col">
                    <span className="d-flex align-items-center">
                        <img alt={this.state.internalKey} className="avatar filter-by-alt" src={this.state.icon}
                             data-filter-by="alt"></img>
                        &nbsp;&nbsp;
                        <a href={this.props.href}>{this.props.internalKey}</a>
                     </span>
                </span>
             </span>
        )
    }
}