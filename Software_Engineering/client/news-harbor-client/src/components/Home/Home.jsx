import { Card, Button, Row, Col, Container, Carousel } from 'react-bootstrap';
import latestHeadlines from '@/assets/latest_headlines.png';
import inNumbers from '@/assets/in_numbers.png';
import customizeFeed from '@/assets/customize_news.png'
import defaultNews from '@/assets/default_news.png';
import { useSelector } from "react-redux"

import '@/components/Home/Home.css'
import { useEffect, useState } from 'react';


function Home() {
    const [latestArticles, setLatestArticles] = useState([]);
    const isDarkMode = useSelector((state) => state.theme.isDarkMode);
    const carousselData = [
        {
            src: latestHeadlines,
            title: "Latest Headlines",
            description: "Stay updated with the latest stories."
        },
        {
            src: inNumbers,
            title: "In Numbers",
            description: "Vizualise insights into the current trends."
        },
        {
            src: customizeFeed,
            title: "Customize your feed",
            description: "Filter News by Topics, Dates, and More for Personalized Insights."
        }
    ];

    const options = { "method": "POST" };

    const openArticle = (id) => {
        const newWindow = window.open(`/article?id=${id}`, '_blank', 'noopener,noreferrer')
        if (newWindow) newWindow.opener = null
    }

    useEffect(() => {

        fetch("/api/articles?limit=6", options)
        .then((response) => response.json())
        .then((data) => setLatestArticles(data["articles"]))
    }, [])

    return (
    <>
        <Carousel>
        {
            carousselData.map((item, idx) => (
                <Carousel.Item key={idx}>
                    <img
                        className="d-block w-100 carousel-image"
                        src={item.src}
                        alt={item.title}
                    />
                    <Carousel.Caption className="carousel-text-container">
                        <h3 className="carousel-text">{item.title}</h3>
                        <p className="carousel-text">{item.description}</p>
                    </Carousel.Caption>
                </Carousel.Item>
            ))
        }
        </Carousel>

        <Container className='mt-2'>
            <h2>Latest News</h2>
            <Row>
                {latestArticles.map((news, idx) => (
                    <Col md={4} key={idx}>
                    <Card className='mb-3' bg={isDarkMode ? 'dark' : 'light'} text={isDarkMode ? 'white' : 'dark'}>
                        <Card.Img variant="top" className="image-container" src={news.images && news.images.length > 0 ? news.images[0] : defaultNews} />
                        <Card.Body >
                            <Card.Title className='card-title'>{news.title}</Card.Title>
                            <Card.Text className="card-text-container">
                                {news.subtitle}
                            </Card.Text>
                            <Container className='d-flex justify-content-center'>
                                <Button variant={isDarkMode?'light':'secondary'} onClick={() => openArticle(news.id)}>
                                    Read More &gt;&gt;
                                </Button>
                            </Container>

                        </Card.Body>
                    </Card>
                    </Col>
                ))}
            </Row>
        </Container>
    </>);
}
  
export default Home;