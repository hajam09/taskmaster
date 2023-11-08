import React, {Component} from "react";


export default class MultipleAvatarEntityComponent extends Component {
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
            <li>
                <a href={this.state.href} data-toggle="tooltip" data-original-title={this.state.internalKey}
                   title={this.state.internalKey}>
                    <img alt={this.state.internalKey} className="avatar filter-by-alt" src={this.state.icon}
                         data-filter-by="alt"></img>
                </a>
            </li>
        )
    }
}