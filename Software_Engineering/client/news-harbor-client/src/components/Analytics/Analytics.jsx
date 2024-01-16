import React, { useEffect, useState } from "react";
import "@/components/Analytics/Analytics.css";
import { Container, Row, Col } from "react-bootstrap";
import GraphBar from "@/components/Analytics/GraphBar/GraphBar";

export const Analytics = () => {
  const [topicsFrequency, setTopicsFrequency] = useState([]);
  const [authorsFrequency, setAuthorsFrequency] = useState([]);
  const [categoriesFrequency, setCategoriesFrequency] = useState([]);
  const [subcategoriesFrequency, setSubcategoriesFrequency] = useState([]);

  useEffect(() => {
    const options = { method: "POST" };

    fetch("/api/topics/frequency", options)
      .then((response) => response.json())
      .then((data) => setTopicsFrequency(data));

    fetch("/api/authors/frequency", options)
      .then((response) => response.json())
      .then((data) => setAuthorsFrequency(data));

    fetch("/api/categories/frequency", options)
      .then((response) => response.json())
      .then((data) => setCategoriesFrequency(data));

    fetch("/api/subcategories/frequency", options)
      .then((response) => response.json())
      .then((data) => setSubcategoriesFrequency(data));
  }, []);

  return (
    <Container className="analytics-content">
      <Container>
        <Row>
          <Col md={12} lg={6}>
            <GraphBar
              data={topicsFrequency}
              containerId="topicsChart"
              label="topic"
              title="Top 10 Topics"
            />
          </Col>

          <Col md={12} lg={6}>
            <GraphBar
              data={authorsFrequency}
              containerId="authorsChart"
              label="author"
              title="Top 10 Authors"
            />
          </Col>
        </Row>
      </Container>

      <Container className="mt-2">
        <Row>
          <Col md={12} lg={6}>
            <GraphBar
              data={categoriesFrequency}
              containerId="categoriesChart"
              label="category"
              title="Top 10 Categories"
            />
          </Col>

          <Col md={12} lg={6}>
            <GraphBar
              data={subcategoriesFrequency}
              containerId="subcategoriesChart"
              label="subcategory"
              title="Top 10 Subcategories"
            />
          </Col>
        </Row>
      </Container>
    </Container>
  );
};
