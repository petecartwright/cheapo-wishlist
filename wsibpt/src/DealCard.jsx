import React, { Component } from "react";
import Spinner from "./Spinner";
import { Thumbnail, Button } from "react-bootstrap";
import styled from "styled-components";

const Image = styled.img`
  width: auto;
  max-height: 20vh;
`;

class DealCard extends Component {
  render() {
    let dealOrSpinner;

    // check to see if we've gotten any props so we can show a loader if not
    // 0 if we have no probs, otherwise we do
    // const noPropsReceivedYet = Object.keys(this.props.deal).length;
    // console.log("noPropsReceivedYet is ");

    if (!this.props.loaded) {
      dealOrSpinner = (
        <Thumbnail>
          <Spinner />
        </Thumbnail>
      );
    } else {
      dealOrSpinner = (
        <Thumbnail src={this.props.deal.mediumImageURL} className="text-left">
          <h3>{this.props.deal.item_name}</h3>
          <p>Only {this.props.deal.offer_price_formatted}!</p>
          <p>
            <Button bsStyle="primary" href={this.props.deal.url}>
              Buy!
            </Button>
          </p>
        </Thumbnail>
      );
    }
    return dealOrSpinner;
  }
}

export default DealCard;
