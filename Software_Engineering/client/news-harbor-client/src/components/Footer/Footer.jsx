import '@/components/Footer/Footer.css'
import { Container, Navbar } from 'react-bootstrap';
import { useSelector } from "react-redux"

function Footer() {
    const isDarkMode = useSelector((state) => state.theme.isDarkMode);

    return (
        <Navbar bg={isDarkMode ? "dark" : "light"} variant={isDarkMode ? "dark" : "light"} >
            <Container>
                <Navbar.Brand />
                <Navbar.Toggle />
                <Navbar.Collapse className="justify-content-end">
                    <Navbar.Text>
                        © 2024 News Harbor
                    </Navbar.Text>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    );
}

export default Footer;
