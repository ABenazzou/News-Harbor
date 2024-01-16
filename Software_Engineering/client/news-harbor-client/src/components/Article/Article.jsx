import React, { useEffect, useState } from 'react'
import { Container, Row, Col, Image, Badge, Modal } from 'react-bootstrap';
import '@/components/Article/Article.css';
import { useSelector } from "react-redux"
import { format } from 'date-fns';

export const Article = () => {
    const [article, setArticle] = useState({});
    const queryParameters = new URLSearchParams(window.location.search)
    const id = queryParameters.get("id");
    const isDarkMode = useSelector((state) => state.theme.isDarkMode);

    const [showModal, setShowModal] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
  
    const handleImageClick = (image) => {
      setSelectedImage(image);
      setShowModal(true);
    };
    
    const formatTextToParagraphs = (text) => {
        // Split text at every ". " followed by a capital letter
        const paragraphs = text.split(/(?<=\.)(?=\s[A-Z])/);
        return paragraphs.map((paragraph, index) => (
            <p key={index}>{paragraph.trim()}</p>
        ));
    };

    const formatDate = (date) => {
        const dateObj = new Date(date);
        const formattedDate = format(dateObj, "do MMMM yyyy");
        return formattedDate
    }

    useEffect(() => {

        fetch(`/api/articles/${id}`)
        .then((response) => response.json())
        .then(data => {
            if(data.images){
                const filteredImages = data.images.filter(image => !image.includes("presentational_grey_line") && !image.includes("_line")); 
                data.images = filteredImages;
            }
            setArticle(data);
        })
    }, [])

    return (
        <Container className="article-body">
            <Row>
                <Col>
                    <h1 className="mb-3 d-flex align-items-center justify-content-center">{article.title}</h1>
                    {article.subtitle && <h4 className="mb-3 muted">{article.subtitle}</h4>}

                    <div className="mb-4">
                        {article.date_posted && <Badge bg="secondary" className="me-2">Posted on: {formatDate(article.date_posted)}</Badge>}
                        {article.category && <Badge bg="info">Category: {article.category}</Badge>}
                        {article.subcategory && <Badge bg="warning" className="ms-2">Subcategory: {article.subcategory}</Badge>}
                    </div>

                    {article.images && article.images.length > 0 && (
                        <div className="mt-1">
                            <Image src={article.images[0]} alt={`image-0`} fluid className="mb-3" />
                        </div>
                    )}

                    {article.authors && article.authors.length > 0 && (
                        <p className="authors">By {article.authors.join(', ')}</p>
                    )}

                    {article.full_text && formatTextToParagraphs(article.full_text)}
                </Col>
            </Row>
            <Row xs={1} md={2} lg={3} className="g-3">

                {article.images && article.images.length > 1 && (
                    article.images.slice(1).map((image, index) => (
                        <Col key={index}>
                            <Image src={image} alt={`image-${index}`} className='image-gallery' onClick={() => handleImageClick(image)} />
                        </Col>
                    ))
                )}
            </Row>
            <Modal show={showModal} onHide={() => setShowModal(false)} centered>
                <Modal.Body>
                    <img src={selectedImage} alt="Full Image" style={{ width: '100%', height: 'auto' }} />
                </Modal.Body>
            </Modal>
            <Row>
                <Col>
                    {article.topics && article.topics.length > 0 && (
                        <div className="mt-4">
                            <strong>Topics:</strong> {article.topics.map((topic, index) => (
                                <Badge key={index} bg={isDarkMode?"light":"dark"} text={isDarkMode?"dark":"light"} className="ms-2 mb-4">{topic}</Badge>
                            ))}
                        </div>
                    )}
                </Col>
            </Row>
        </Container>
        
    )
}
