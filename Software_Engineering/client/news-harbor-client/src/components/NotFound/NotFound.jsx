import { Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import "@/components/NotFound/NotFound.css";

function NotFound() {
  return (
    <Container className="not-found">
      <h1>Oops! You seem to be lost.</h1>
      <p>Here are some helpful links:</p>
      <Link to="/">Home</Link>
    </Container>
  );
}

export default NotFound;
