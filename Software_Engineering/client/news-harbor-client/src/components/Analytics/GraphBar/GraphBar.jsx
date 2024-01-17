import React, { useEffect } from "react";
import * as d3 from "d3";
import { useSelector } from "react-redux";
import "@/components/Analytics/GraphBar/GraphBar.css";

const GraphBar = ({ data, containerId, label, title }) => {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);
  const colorDark = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => d["count"])])
    .range(["#ffafbd", "#ffc3a0"]); // orange for dark bg

  const colorLight = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => d["count"])])
    .range(["#6a85b6", "#bac8e0"]); // light blue for light bg

  var color = isDarkMode ? colorDark : colorLight;

  useEffect(() => {
    setTimeout(() => {
      const style = getComputedStyle(document.documentElement);
      const foregroundColor = style.getPropertyValue("--foreground-color");
      d3.select(`#${containerId} svg g text.title`).style(
        "fill",
        foregroundColor
      );
    }, 100); // delay 100 ms for dom colors to refresh

    color = isDarkMode ? colorDark : colorLight;

    d3.select(`#${containerId}`)
      .selectAll(".bar")
      .data(data)
      .attr("fill", (d) => color(d["count"]));
  }, [isDarkMode]);

  useEffect(() => {
    const style = getComputedStyle(document.documentElement);
    const foregroundColor = style.getPropertyValue("--foreground-color");

    const margin = { top: 20, right: 20, bottom: 80, left: 40 };
    const width = 500 - margin.left - margin.right; // max width - spacing
    const height = 400 - margin.top - margin.bottom; // nax height - spacing

    // remove nd recreate for no duplicates, to check if i can improve this
    d3.select(`#${containerId}`).select("svg").remove();

    let svg = d3
      .select(`#${containerId}`)
      .append("svg")
      .attr("style", `outline: thin solid ${foregroundColor}; padding: 10px; border-radius: 10%; margin-bottom: 10px`)
      .attr("width", width + margin.left + margin.right) // svg width = initial vals 500 400
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left}, ${margin.top})`); // moving the group with ml mt

    // domain is the expected range of the data
    // range is the renderd values/pixel pos -> {domain: range}

    const x = d3
      .scaleBand()
      .range([0, width])
      .domain(data.map((d) => d[label]))
      .padding(0.1);
    // divide the x bar on domain throughout range

    const y = d3
      .scaleLinear()
      .range([height, 0])
      .domain([0, d3.max(data, (d) => d["count"])]);
    // y divided on domain max vlues throughout range

    svg
      .append("g")
      .attr("transform", `translate(0, ${height})`) // translate the position to the bottom before calling the bar
      .call(d3.axisBottom(x))
      .selectAll("text")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", "-.5em")
      .attr("transform", "rotate(-90)");
    // x axis bar

    svg.append("g").call(d3.axisLeft(y));
    // y axis

    const tooltip = d3
      .select("body")
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);
    // tooltip divs to start transitionning it on graph

    svg
      .selectAll(".bar") // select all existing bar
      .data(data)
      .enter()
      .append("rect") // enter for none existing bar classes and add rect
      .attr("class", "bar")
      .attr("x", (d) => x(d[label])) // map with the scale
      .attr("width", x.bandwidth())
      .attr("y", y(0)) // init as 0 to make the transition
      .attr("height", 0) // init as 0 to make the transition
      .attr("fill", (d) => color(d["count"]))
      .on("mouseover", function (event, d) {
        tooltip.transition().duration(200).style("opacity", 0.9); // make it visible
        tooltip
          .html(`${d["count"]}`)
          .style("left", event.pageX + "px")
          .style("top", event.pageY - 20 + "px");
      })
      .on("mouseout", function (d) {
        tooltip.transition().duration(500).style("opacity", 0); // hide
      })
      .transition()
      .duration(800)
      .attr("y", (d) => y(d["count"])) // map with teh scale
      .attr("height", (d) => height - y(d["count"]));

    svg
      .append("text") // title
      .attr("x", width / 2)
      .attr("y", 0 - margin.top / 2)
      .attr("class", "title")
      .attr("text-anchor", "middle")
      .style("font-size", "14px")
      .style("text-decoration", "underline")
      .style("fill", foregroundColor) // Set the color of the title
      .text(title);
  }, [data, containerId, label]);
  
  return <div className="graph" id={containerId}></div>;
};

export default GraphBar;
