import "@/App.css";
import Header from "@/components/Header/Header";
import Footer from "@/components/Footer/Footer";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "@/components/Home/Home";
import Harbor from "@/components/Harbor/Harbor";
import { useSelector } from "react-redux";
import { useEffect } from "react";
import { darkThemeStyles, lightThemeStyles } from "@/themes";
import { Container } from "react-bootstrap";
import NotFound from "@/components/NotFound/NotFound";
import { Article } from "@/components/Article/Article";
import { Analytics } from "@/components/Analytics/Analytics";
import { Network } from "@/components/Network/Network";

function App() {
  const isDarkMode = useSelector((state) => state.theme.isDarkMode);

  const updateThemeStyles = (isDarkMode) => {
    const theme = isDarkMode ? darkThemeStyles : lightThemeStyles;
    Object.entries(theme).forEach(([property, value]) => {
      document.documentElement.style.setProperty(property, value);
    });
  };

  useEffect(() => {
    updateThemeStyles(isDarkMode);
  }, [isDarkMode]);

  return (
    <Router>
      <Header />
      <Container className="wrapper-container" fluid>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/harbor" element={<Harbor />} />
          <Route path="/article" element={<Article />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/network" element={<Network />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Container>

      <Footer />
    </Router>
  );
}


export default App;
