def test_list_categories_valid(client):
    
    response = client.post("/api/categories")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "category" in response_json
    

def test_list_categories_valid_with_params(client):
    
    test_params = {
        "topics": "Ethiopia",
        "subcategories": "Africa",
    }
    
    query_params = []
    for key, value in test_params.items():
        if isinstance(value, list):
            for item in value:
                query_params.append(f"{key}={item}")
        else:
            query_params.append(f"{key}={value}")
            
    query_string = '&'.join(query_params)
    
    response = client.post(f"/api/categories?{query_string}", json=test_params)
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "category" in response_json
    

def test_list_categories_frequency_valid(client):
    
    response = client.post("/api/categories/frequency")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    

def test_list_categories_frequency_valid_with_params(client):
    
    test_params = {
        "topics": "Ethiopia",
        "subcategories": "Africa",
    }
    
    query_params = []
    for key, value in test_params.items():
        if isinstance(value, list):
            for item in value:
                query_params.append(f"{key}={item}")
        else:
            query_params.append(f"{key}={value}")
            
    query_string = '&'.join(query_params)
    
    response = client.post(f"/api/categories/frequency?{query_string}", json=test_params)
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
