import React, { Component } from "react";
import { Grid, Row, Col, Image, PageHeader } from "react-bootstrap";
import axios from "axios";
import Header from "./Header";
import "./App.css";
import DealCard from "./DealCard";

class BestDeals extends Component {
  state = {
    cheapest_vs_list: {},
    cheapest_vs_list_loaded: false,
    cheapest_overall: {},
    cheapest_overall_loaded: false
  };

  componentDidMount() {
    console.log("AXIOS - about to get cheapest_vs_list");
    axios.get("http://localhost:5000/items/cheapest_vs_list").then(response => {
      console.log("AXIOS - got cheapest_vs_list");
      this.setState({
        cheapest_vs_list_loaded: true,
        cheapest_vs_list: response.data
      });
    });

    console.log("AXIOS - about to get cheapest_overall");
    axios.get("http://localhost:5000/items/cheapest_overall").then(response => {
      console.log("AXIOS - got cheapest_overall");
      this.setState({
        cheapest_overall_loaded: true,
        cheapest_overall: response.data
      });
    });
  }

  render() {
    return (
      <div>
        <Header />
        <Grid>
          <Row>
            <Col xs={12} md={6}>
              <DealCard
                className="cheapest-vs-list"
                deal={this.state.cheapest_vs_list}
                loaded={this.state.cheapest_vs_list_loaded}
              />
            </Col>
            <Col xs={12} md={6}>
              <DealCard
                className="cheapest-overall"
                deal={this.state.cheapest_overall}
                loaded={this.state.cheapest_overall_loaded}
              />
            </Col>
            {/* <Col xs={12} md={4}>
              <DealCard />
            </Col> */}
          </Row>
        </Grid>
      </div>
    );
  }
}

export default BestDeals;
