import React, { useEffect, useState } from "react";
import { Container, Row, Col, ListGroup } from "react-bootstrap";
import "@/components/Network/Network.css";

export const Network = () => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [dimensions, setDimensions] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  const legendData = [
    { group: "Top Authors", color: "green" },
    { group: "Consistent Authors", color: "yellow" },
    { group: "Collaborative Authors", color: "red" },
  ];

  useEffect(() => {
    fetch("/api/authors/network")
      .then((response) => response.json())
      .then((data) => {
        setNodes(data["nodes"]);
        setLinks(data["links"]);
      });

    const handleResize = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener("resize", handleResize);

    return () => {
      // on unmount/rerender
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  useEffect(() => {
    d3.select("#network-container")
      .select("svg")
      .attr("width", dimensions.width)
      .attr("height", dimensions.height);
  }, [dimensions]);

  useEffect(() => {
    d3.select("#network-container").select("svg").remove();
    const { width, height } = dimensions;

    const svg = d3
      .select("#network-container")
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .call(
        d3.zoom().on("zoom", (event) => {
          svg.attr("transform", event.transform);
        })
      )
      .append("g");

    const simulation = d3
      .forceSimulation()
      .force(
        "link",
        d3.forceLink().id((d) => d.id)
      )
      .force("charge", d3.forceManyBody())
      .force("center", d3.forceCenter(width / 2, height / 2));
    // force attractions and repulsions and center graph to center of svg

    // draw lines for each link from our data
    const link = svg
      .append("g")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke-width", 1)
      .attr("stroke", "gray");

    // set the radius of our nodes as per degrees
    const radiusScale = d3
      .scaleSqrt()
      .domain([d3.min(nodes, (d) => d.degree), d3.max(nodes, (d) => d.degree)])
      .range([5, 20]);

    // add circles for our nodes
    const node = svg
      .append("g")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", (d) => radiusScale(d.degree))
      .attr("fill", function (d) {
        if (d.group === "top authors") {
          return "green";
        } else if (d.group === "consistent authors") {
          return "yellow";
        } else if (d.group === "collaborative authors") {
          return "red";
        } else {
          return "grey";
        }
      })
      .call(
        d3
          .drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      );

    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart(); // heat up
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0); // halt
      d.fx = null;
      d.fy = null;
    }

    // add labels
    const labels = svg
      .append("g")
      .attr("class", "labels")
      .selectAll("text")
      .data(
        nodes.filter((d) =>
          [
            "top authors",
            "consistent authors",
            "collaborative authors",
          ].includes(d.group)
        )
      )
      .enter()
      .append("text")
      .attr("dx", 12)
      .attr("dy", ".35em")
      .text((d) => d.id);

    // define the ticked function for the simulation. tick updates pos of nodes and links
    simulation.nodes(nodes).on("tick", ticked);
    simulation.force("link").links(links);

    function ticked() {
      // set correct nodes linking
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      // set correct data point
      node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);

      // set correct label pos
      labels.attr("x", (d) => d.x).attr("y", (d) => d.y);
    }
  }, [nodes, links]);

  return (
    <Container className="network" fluid>
      <Row>
        <Col md={2} className="d-flex align-items-center">
          <ListGroup>
            {legendData.map((item, index) => (
              <ListGroup.Item key={index} className="d-flex align-items-center">
                <span
                  className="legend-color-box"
                  style={{ backgroundColor: item.color }}
                ></span>
                <span className="ms-2">{item.group}</span>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Col>
        <Col md={10}>
          <div
            id="network-container"
            style={{ width: "100%", height: "500px" }}
          ></div>
        </Col>
      </Row>
    </Container>
  );
};
