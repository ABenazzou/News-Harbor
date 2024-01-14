def test_list_articles_raw_valid(client):
    
    response = client.post("/api/articles")
    assert response.status_code == 200
    assert "articles" in response.json()


def test_list_articles_invalid_limit(client):
    
    response = client.post("/api/articles?limit=0")
    assert response.status_code == 400


def test_list_articles_invalid_offset(client):
    
    response = client.post("/api/articles?offset=-1")
    assert response.status_code == 400
    

def test_list_articles_invalid_sort_order(client):
    
    response = client.post("/api/articles?sort_order=invalid")
    assert response.status_code == 400


def test_list_articles_valid_with_parameters(client):
    test_params = {
        "offset": 1,
        "limit": 3,
        "sort_by": "title",
        "sort_order": "asc",
        "categories": "World",
        "subcategories": "Africa",
        "authors": ["Damian Zane", "PA Media"],
        "topics": "Ethiopia",
        "date_posted": "2024-01-09"
    }
    
    query_params = []
    for key, value in test_params.items():
        if isinstance(value, list):
            for item in value:
                query_params.append(f"{key}={item}")
        else:
            query_params.append(f"{key}={value}")
            
    query_string = '&'.join(query_params)
    
    response = client.post(f"/api/articles?{query_string}", json=test_params)
    assert response.status_code == 200
    assert "articles" in response.json()
    