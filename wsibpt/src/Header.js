import React from "react";
import { Image, PageHeader } from "react-bootstrap";
import header from "./header.png";
import "./App.css";

const Header = () => (
  <PageHeader>
    <div className="header-image-wrapper">
      <Image
        style={{ maxHeight: "20vh" }}
        src={header}
        alt="what should I buy pete today"
        rounded
      />
    </div>
  </PageHeader>
);

export default Header;
