import React, { useState } from "react";
import {
  Navbar,
  Nav,
  Form,
  FormControl,
  Button,
  Container,
} from "react-bootstrap";
import { useSelector, useDispatch } from "react-redux";
import { toggle } from "@/redux/features/theme/themeSlice";
import { NavLink } from "react-router-dom";
import { BsMoonStarsFill, BsFillSunFill } from "react-icons/bs";
import "@/components/Header/Header.css";
import brandLogo from "@/assets/NavBrand.png";
import { useNavigate, useLocation } from "react-router-dom";

function Header() {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const [searchText, setSearchText] = useState("");
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const location = useLocation();

  const handleSearch = (e) => {
    e.preventDefault();

    navigate("/harbor?search", {
      state: {
        searchText: searchText,
      },
    });
    setSearchText("");
  };

  return (
    <Navbar
      bg={isDarkMode ? "dark" : "light"}
      variant={isDarkMode ? "dark" : "light"}
      expand="lg"
      className="fixed-top"
    >
      <Container>
        <Navbar.Brand as={NavLink} to="/">
          <img
            src={brandLogo}
            width="40"
            height="40"
            className="d-inline-block align-top"
            alt="News Harbor"
          />
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse
          id="basic-navbar-nav"
          className="justify-content-between"
        >
          <Nav className="me-auto">
            <Nav.Link
              as={NavLink}
              to="/"
              className={
                location.pathname === "/" && location.search === ""
                  ? "active-custom"
                  : "inactive-custom"
              }
            >
              Home
            </Nav.Link>
            <Nav.Link
              as={NavLink}
              to="/harbor"
              className={
                location.pathname === "/harbor" && location.search === ""
                  ? "active-custom"
                  : "inactive-custom"
              }
            >
              Harbor
            </Nav.Link>
            <Nav.Link
              as={NavLink}
              to="/analytics"
              className={
                location.pathname === "/analytics" && location.search === ""
                  ? "active-custom"
                  : "inactive-custom"
              }
            >
              Analytics
            </Nav.Link>
            <Nav.Link
              as={NavLink}
              to="/network"
              className={
                location.pathname === "/neywork" && location.search === ""
                  ? "active-custom"
                  : "inactive-custom"
              }
            >
              Network
            </Nav.Link>
          </Nav>

          <Container className="d-flex align-items-left mb-2" id="darkmode">
            <input
              type="checkbox"
              className="checkbox"
              id="checkbox"
              onChange={() => dispatch(toggle())}
              checked={!isDarkMode}
            />
            <label htmlFor="checkbox" className="label">
              <BsMoonStarsFill color="white" />
              <BsFillSunFill color="yellow" />
              <div className="ball"></div>
            </label>
          </Container>

          <FormControl
            type="search"
            placeholder="Search"
            className="me-2"
            aria-label="Search"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSearch(e);
              }
            }}
          />
          <Button variant="outline-success" onClick={handleSearch}>
            Search
          </Button>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Header;
