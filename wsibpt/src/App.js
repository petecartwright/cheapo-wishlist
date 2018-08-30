import React, { Component } from "react";
import { BrowserRouter, Switch, Route } from "react-router-dom";
import BestDeals from "./BestDeals";
import AllDeals from "./AllDeals";
import "./App.css";

const FourOhFour = () => <h1>404</h1>;

const App = () => (
  <BrowserRouter>
    <div className="app">
      <Switch>
        <Route exact path="/" component={BestDeals} />
        <Route exact path="/all" component={AllDeals} />
        <Route component={FourOhFour} />
      </Switch>
    </div>
  </BrowserRouter>
);

export default App;
