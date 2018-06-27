import React, { Component } from 'react';
import logo from './logo.svg';

import {Tooltip, OverlayTrigger} from 'react-bootstrap';
import PropTypes from 'prop-types';

import FilterableSortableTable from './ReactFilterableSortableTable.js'; 
import moment from 'moment';

import './App.css';


function cleanUpOfferData(offers){
  // update the model name
  // generate a google maps link + a href
  // generate a phone href
  // put the columns in the right order with the right names
  var cleaned_offers = [];

  offers.forEach((offer, index) => {
    cleaned_offers.push({'Item Name': `<a href=${offer.url}>${offer.item_name}</a>`,
                         'Prime Eligible?': offer.prime_eligible,
                         'List Price': offer.list_price_formatted,
                         'Offer Price': offer.offer_price_formatted,
                         'Savings Vs List': offer.savings_vs_list,
                         'key': index.toString()
                         });
  });
  return cleaned_offers;
}


class App extends Component {

  constructor(props){
    super(props);
    this.state = {table_data: null}

    this.componentDidMount = this.componentDidMount.bind(this);
  }

  componentDidMount(){
    var self = this;
    fetch('http://localhost:5000/items/all')
            .then(function (response) {
                if (response.status !== 200){
                  console.log("There's a problem. :(");
                  return;
                }

                response.json().then(function(data){
                  let offers = data['results'];
                  console.log('offers is');
                  console.log(offers);  
                  var cleaned_offers = cleanUpOfferData(offers)
                  self.setState({table_data: cleaned_offers}, function(){console.log('state is updated!')});
              })
            });    
  }


  render() {
    return (
      <div className="App">
        <header className="App-header">
          <img src={logo} className="App-logo" alt="logo" />
          <h1 className="App-title">Welcome to React</h1>
        </header>
        <p className="App-intro">
          To get started, edit <code>src/App.js</code> and save to reload.
        </p>
        
          <FilterableSortableTable table_data={ this.state.table_data } records_per_page={50}/>
        
      </div>
    );
  }
}

export default App;
