import React, { Component } from "react";
import { Table, Row, Col, Image } from "react-bootstrap";
import axios from "axios";
import Header from "./Header";
import "./App.css";

class AllDeals extends Component {
  state = {
    all_deals: [],
    all_deals_loaded: false
  };

  componentDidMount() {
    console.log("AXIOS - about to get cheapest_vs_list");
    axios.get("http://localhost:5000/items/all").then(response => {
      console.log("AXIOS - got all deals");
      console.log(response.data);
      this.setState({
        all_deals_loaded: true,
        all_deals: response.data.results
      });
    });
  }

  render() {

    return (
      <div>
        <Header />
        <Table striped bordered condensed hover>
          <thead>
            <tr>
              <th>Item Name</th>
              <th>List Price</th>
              <th>Savings Vs List</th>
            </tr>
          </thead>
          <tbody>
            {this.state.all_deals.map(deal => (
              <tr>
                <td>
                  <a href={deal.url}>{deal.item_name}</a>
                </td>
                <td>{deal.list_price}</td>
                <td>{deal.savings_vs_list}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    );
  }
}

export default AllDeals;
