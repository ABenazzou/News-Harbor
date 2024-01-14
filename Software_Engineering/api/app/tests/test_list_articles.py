def test_list_articles_raw_valid(client):
    
    response = client.post("/articles")
    assert response.status_code == 200
    assert "articles" in response.json()


def test_list_articles_invalid_limit(client):
    
    response = client.post("/articles?limit=0")
    assert response.status_code == 400


def test_list_articles_invalid_offset(client):
    
    response = client.post("/articles?offset=-1")
    assert response.status_code == 400
    

def test_list_articles_invalid_sort_order(client):
    
    response = client.post("/articles?sort_order=invalid")
    assert response.status_code == 400


def test_list_articles_valid_with_parameters(client):
    test_params = {
        "offset": 1,
        "limit": 3,
        "sort_by": "title",
        "sort_order": "asc",
        "category": "World",
        "subcategory": "Africa",
        "author": "Damian Zane",
        "topic": "Ethiopia",
        "date_posted": "2024-01-09"
    }
    query_params = '&'.join([f"{k}={v}" for k,v in test_params.items()])
    
    response = client.post(f"/articles?{query_params}", json=test_params)
    assert response.status_code == 200
    assert "articles" in response.json()
    