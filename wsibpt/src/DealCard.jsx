import React, { Component } from "react";
import Spinner from "./Spinner";
import { Thumbnail, Button } from "react-bootstrap";

class DealCard extends Component {
  render = () =>
    this.props.loaded ? (
      <div className="deal-card">
        <div className="card-image-container">
          <img src={this.props.deal.mediumImageURL} />
        </div>
        <div className="card-text-container">
          <h3>{this.props.deal.item_name}</h3>
          <h2>{this.props.deal.offer_price_formatted}</h2>
        </div>
      </div>
    ) : (
      <Thumbnail>
        <Spinner />
      </Thumbnail>
    );
}

export default DealCard;
