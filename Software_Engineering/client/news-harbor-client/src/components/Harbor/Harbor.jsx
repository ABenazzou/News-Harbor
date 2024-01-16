import React, { useState, useEffect, useRef  } from 'react';
import { Card, Button, Form, Container, Row, Col } from 'react-bootstrap';
import Select from 'react-select';
import makeAnimated from 'react-select/animated';
import ReactPaginate from 'react-paginate';
import '@/components/Harbor/Harbor.css'
import defaultNews from '@/assets/default_news.png';
import { useSelector } from "react-redux"

import { DateRangePicker } from 'rsuite';
import { useLocation } from 'react-router-dom';


const Harbor = () => {
    const [itemsPerPage, setItemsPerPage] = useState(6);
    const location = useLocation();
    const searchText = location.state?.searchText || '';

    const authorSelectRef = useRef();
    const dateSelectRef = useRef();
    const categorySelectRef = useRef();
    const subcategorySelectRef = useRef();
    const topicSelectRef = useRef();

    const isDarkMode = useSelector((state) => state.theme.isDarkMode);
    const [currentPageItems, setCurrentPageItems] = useState([]);
    const [offset, setOffset] = useState(0);
    const [pageCount, setPageCount] = useState(0);

    const [categories, setCategories] = useState([]);
    const [subcategories, setSubcategories] = useState([]);
    const [topics, setTopics] = useState([]); 
    const [authors, setAuthors] = useState([]);

    const [categoryOptions, setCategoryOptions] = useState([]);
    const [subcategoryOptions, setSubcategoryOptions] = useState([]);
    const [topicOptions, setTopicOptions] = useState([]);
    const [authorOptions, setAuthorOptions] = useState([]);

    // filters
    const [filterCategories, setFilterCategories] = useState([]);
    const [filterSubcategories, setFilterSubcategories] = useState([]);
    const [filterTopics, setFilterTopics] = useState([]); 
    const [filterAuthors, setFilterAuthors] = useState([]);

    const [filterStartDate, setFilterStartDate] = useState(null);
    const [filterEndDate, setFilterEndDate] = useState(null);

    const [filterQuery, setFilterQuery] = useState('');
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [selectedDateRange, setSelectedDateRange] = useState(null);

    const animatedComponents = makeAnimated();

    const [showFilters, setShowFilters] = useState(false);

    const toggleFilters = () => {
      setShowFilters(!showFilters);
    };

    const openArticle = (id) => {
      const newWindow = window.open(`/article?id=${id}`, '_blank', 'noopener,noreferrer')
      if (newWindow) newWindow.opener = null
  }

    const formGroups = [
      { controlId: "categories", label: "Categories", options: categoryOptions, setter: setFilterCategories, ref: categorySelectRef },
      { controlId: "subcategories", label: "Subcategories", options: subcategoryOptions, setter: setFilterSubcategories, ref: subcategorySelectRef },
      { controlId: "topicsSelect", label: "Topics", options: topicOptions, setter: setFilterTopics, ref: topicSelectRef },
      { controlId: "authorsSelect", label: "Authors", options: authorOptions, setter: setFilterAuthors, ref: authorSelectRef}
    ];

    const handlePageClick = (event) => {
        setOffset(event.selected * itemsPerPage)
    };

    const resetFilters = () => {

      formGroups.forEach(group => {
        group.ref.current.clearValue();
      });

      setSelectedDateRange(null);
      setFilterStartDate(null);
      setFilterEndDate(null);
    }

    const handleDateChange = (range) => {
      setSelectedDateRange(range);

      const formatDateAndSet = (date, setDate) => {
        if (date) {
          const isoDate = formatDate(date);
          setDate(isoDate);
        } else {
          setDate(null);
        }
      };


      if (range) {
        formatDateAndSet(range[0], setFilterStartDate);
        formatDateAndSet(range[1], setFilterEndDate);
      } else {
        setFilterStartDate(null);
        setFilterEndDate(null);
      }
    }

    const formatDate = (date) => {
      // UTC +1 issue reverts one day in date picker
      const newDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60 * 1000)); 

      const isoString = newDate.toISOString();
      return isoString.slice(0, 10);
    };
      
    useEffect(() => {
      const options = searchText === ''? {
        "method": "POST",
      } : {
          "method": "POST",
          "headers": { 'Content-Type': 'application/json' },
          "body": JSON.stringify({ full_text_search: searchText })
      };

      fetch(`/api/articles?limit=${itemsPerPage}&offset=${offset}&${filterQuery}`, options)
      .then((response) => response.json())
      .then((data) => { 
          setPageCount(Math.ceil(data["total"] / itemsPerPage));
          setCurrentPageItems(data["articles"]);
      });
      
    }, [offset, refreshTrigger, searchText]);

    useEffect(() => {

      const options = searchText === ''? {
        "method": "POST",
      } : {
          "method": "POST",
          "headers": { 'Content-Type': 'application/json' },
          "body": JSON.stringify({ full_text_search: searchText })
      };

      fetch(`/api/authors`, options)
      .then((response) => response.json())
      .then((data) => { 
        setAuthors(data["authors"]);
      });
      
      fetch(`/api/topics`, options)
      .then((response) => response.json())
      .then((data) => { 
        setTopics(data["topics"]);
      });

      fetch(`/api/categories`, options)
      .then((response) => response.json())
      .then((data) => { 
        setCategories(data["category"]);
      });

      fetch(`/api/subcategories`, options)
      .then((response) => response.json())
      .then((data) => { 
        setSubcategories(data["subcategory"]);
      });
      
  }, [searchText]);

  useEffect(() => {
    const options = searchText === ''? {
      "method": "POST",
    } : {
        "method": "POST",
        "headers": { 'Content-Type': 'application/json' },
        "body": JSON.stringify({ full_text_search: searchText })
    };

    const authorsQuery = filterAuthors.map(author => `authors=${author}`).join('&');
    const subcategoriesQuery = filterSubcategories.map(subcategory => `subcategories=${subcategory}`).join('&');
    const topicsQuery = filterTopics.map(topic => `topics=${topic}`).join('&');

    const categoriesFilterQuery = [authorsQuery, subcategoriesQuery, topicsQuery].filter(query => query !== '');
    const categoriesFilterQueryString = categoriesFilterQuery.join('&');

    fetch(`/api/categories?${categoriesFilterQueryString}`, options)
    .then((response) => response.json())
    .then((data) => setCategories(data["category"]))

  }, [filterAuthors, filterTopics, filterSubcategories])

  useEffect(() => {
    const options = searchText === ''? {
      "method": "POST",
    } : {
        "method": "POST",
        "headers": { 'Content-Type': 'application/json' },
        "body": JSON.stringify({ full_text_search: searchText })
    };

    const authorsQuery = filterAuthors.map(author => `authors=${author}`).join('&');
    const categoriesQuery = filterCategories.map(category => `categories=${category}`).join('&');
    const subcategoriesQuery = filterSubcategories.map(subcategory => `subcategories=${subcategory}`).join('&');

    const topicsFilterQuery = [authorsQuery, subcategoriesQuery, categoriesQuery].filter(query => query !== '');
    const topicsFilterQueryString = topicsFilterQuery.join('&');

    fetch(`/api/topics?${topicsFilterQueryString}`, options)
    .then((response) => response.json())
    .then((data) => setTopics(data["topics"]))

  }, [filterAuthors, filterCategories, filterSubcategories])
  
  useEffect(() => {
    const options = searchText === ''? {
      "method": "POST",
    } : {
        "method": "POST",
        "headers": { 'Content-Type': 'application/json' },
        "body": JSON.stringify({ full_text_search: searchText })
    };

    const authorsQuery = filterAuthors.map(author => `authors=${author}`).join('&');
    const categoriesQuery = filterCategories.map(category => `categories=${category}`).join('&');
    const topicsQuery = filterTopics.map(topic => `topics=${topic}`).join('&');

    const subCategoriesFilterQuery = [authorsQuery, categoriesQuery, topicsQuery].filter(query => query !== '');
    const subCategoriesFilterQueryString = subCategoriesFilterQuery.join('&');

    fetch(`/api/subcategories?${subCategoriesFilterQueryString}`, options)
    .then((response) => response.json())
    .then((data) => setSubcategories(data["subcategory"]))

  }, [filterAuthors, filterCategories, filterTopics])

  useEffect(() => {
    const options = searchText === ''? {
      "method": "POST",
    } : {
        "method": "POST",
        "headers": { 'Content-Type': 'application/json' },
        "body": JSON.stringify({ full_text_search: searchText })
    };

    const categoriesQuery = filterCategories.map(category => `categories=${category}`).join('&');
    const subcategoriesQuery = filterSubcategories.map(subcategory => `subcategories=${subcategory}`).join('&');
    const topicsQuery = filterTopics.map(topic => `topics=${topic}`).join('&');

    const authorsFilterQuery = [categoriesQuery, subcategoriesQuery, topicsQuery].filter(query => query !== '');
    const authorsFilterQueryString = authorsFilterQuery.join('&');

    fetch(`/api/authors?${authorsFilterQueryString}`, options)
    .then((response) => response.json())
    .then((data) => setAuthors(data["authors"]))

  }, [filterSubcategories, filterCategories, filterTopics])

  useEffect(()=>{
    setAuthorOptions(authors.map(item => ({ value: encodeURIComponent(item), label: item })));
  }, [authors])

  useEffect(()=>{
    setCategoryOptions(categories.map(item => ({ value: encodeURIComponent(item), label: item })));
  }, [categories])

  useEffect(()=>{
    setSubcategoryOptions(subcategories.map(item => ({ value: encodeURIComponent(item), label: item })));
  }, [subcategories])

  useEffect(()=>{
    setTopicOptions(topics.map(item => ({ value: encodeURIComponent(item), label: item })));
  }, [topics])
  
  useEffect(() => {

    const authorsQuery = filterAuthors.map(author => `authors=${author}`).join('&');
    const categoriesQuery = filterCategories.map(category => `categories=${category}`).join('&');
    const subcategoriesQuery = filterSubcategories.map(subcategory => `subcategories=${subcategory}`).join('&');
    const topicsQuery = filterTopics.map(topic => `topics=${topic}`).join('&');

    let dateQuery = "";
    if (filterStartDate) dateQuery += `start_date=${filterStartDate}`;

    if (filterEndDate) {
      if (dateQuery.length > 0 ) {
        dateQuery += "&";
      }
      dateQuery += `end_date=${filterEndDate}`
    }

    const filterQuery = [authorsQuery, categoriesQuery, subcategoriesQuery, topicsQuery, dateQuery].filter(query => query !== '');
    const filterQueryString = filterQuery.join('&');
    setFilterQuery(filterQueryString);

    if (offset === 0) setRefreshTrigger(prev => prev + 1);
    else setOffset(0);
    
}, [filterAuthors, filterCategories, filterSubcategories, filterTopics, filterStartDate, filterEndDate]);


  return (
    <Container className='body-content'>

      { searchText !== '' &&
        <Row className='mb-2 mt-1'>
          <Col md={12} className='search-results'>
            Search Results for text : {searchText}
          </Col>
        </Row>

      }

      <Row className="mb-2 d-md-none">
        <Col>
          <Button onClick={toggleFilters} className='theme-button'>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </Button>
        </Col>
      </Row>
      <Row className={`mb-4 ${showFilters ? '' : 'd-none d-md-flex'}`}>
        <Col md={3}>
          <Form.Group controlId="datePicker" className='date-range'>
                <Form.Label>Date Range</Form.Label>
                <DateRangePicker 
                  onChange={handleDateChange}
                  value={selectedDateRange}
                  ref={dateSelectRef}
                />
            </Form.Group>
        </Col>
        {formGroups.map((group, idx) => (
          <Col md={2} key={idx}>
            <Form.Group controlId={group.controlId} key={group.controlId}>
              <Form.Label>{group.label}</Form.Label>
              <Select
                components={animatedComponents}
                ref={group.ref}
                isMulti
                options={group.options}
                className="basic-multi-select"
                classNamePrefix="select"
                value={group.selectedState}
                onChange={(selected) => group.setter(selected.map(option => option.value))}
                styles={{
                  control: (base) => ({
                    ...base,
                    background: 'var(--background-color)',  
                    color: 'red',
                  }),
                  option: (base) => ({
                    ...base,
                    cursor: "pointer",
                    background: 'var(--background-color)',
                    ":hover": {
                      backgroundColor: "var(--hover-background-color)",
                    },
                  })
                }}
              />
            </Form.Group>
          </Col>
          ))}
          <Col md={1} className='mt-3'>
            <Button onClick={resetFilters} variant={isDarkMode?'light':'dark'}> Reset Filters </Button>
          </Col>
      </Row>

      <Row>
        <Row>
          {currentPageItems.map((news, idx) => (
              <Col md={4} key={idx}>
                  <Card className='mb-3' bg={isDarkMode ? 'dark' : 'light'} text={isDarkMode ? 'white' : 'dark'}>
                      <Card.Img variant="top" className="image-container" src={news.images && news.images.length > 0 ? news.images[0] : defaultNews} />
                      <Card.Body >
                          <Card.Title className='card-title'>{news.title}</Card.Title>
                          <Card.Text className="card-text-container">
                              {news.subtitle}
                          </Card.Text>
                          <Container className='d-flex justify-content-center'>
                            <Button variant={isDarkMode?'light':'secondary'} onClick={() => openArticle(news.id)}>Read More &gt;&gt;
                            </Button>
                          </Container>
                      </Card.Body>
                  </Card>
              </Col>
          ))}

          <Container className="pagination-container">
          
              <ReactPaginate
                  breakLabel="..."
                  nextLabel=">"
                  onPageChange={handlePageClick}
                  pageRangeDisplayed={3}
                  marginPagesDisplayed={2}
                  pageCount={pageCount}
                  previousLabel="<"
                  renderOnZeroPageCount={null}

                  containerClassName="pagination"
                  pageClassName="page-item"
                  pageLinkClassName="page-link"
                  previousClassName="page-item"
                  previousLinkClassName="page-link"
                  nextClassName="page-item"
                  nextLinkClassName="page-link"
                  breakClassName="page-item"
                  breakLinkClassName="page-link"
                  activeClassName="active"
              />

          </Container>
        </Row>
      </Row>
    </Container>
  );
};

export default Harbor;
