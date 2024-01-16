def test_list_topics_valid(client):
    
    response = client.post("/api/topics")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "topics" in response_json
    

def test_list_topics_valid_with_params(client):
    
    test_params = {
        "categories": "World",
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
    
    response = client.post(f"/api/topics?{query_string}", json=test_params)
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "topics" in response_json
    
    
def test_list_topics_frequency_valid(client):
    
    response = client.post("/api/topics/frequency")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    

def test_list_topics_frequency_valid_with_params(client):
    
    test_params = {
        "categories": "World",
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
    
    response = client.post(f"/api/topics/frequency?{query_string}", json=test_params)
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    

def test_list_topics_trends_valid_with_params(client):
    
    test_params = {
        "categories": "World",
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
    
    response = client.post(f"/api/topics/trends?{query_string}", json=test_params)
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    
    
def test_list_topics_trends_valid(client):
    
    response = client.post("/api/topics/trends")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)