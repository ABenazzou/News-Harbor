def test_list_subcategories_valid(client):
    
    response = client.post("/api/subcategories")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "subcategory" in response_json
    

def test_list_subcategories_valid_with_params(client):
    
    test_params = {
        "categories": "World",
        "topics": "Ethiopia",
    }
    
    query_params = []
    for key, value in test_params.items():
        if isinstance(value, list):
            for item in value:
                query_params.append(f"{key}={item}")
        else:
            query_params.append(f"{key}={value}")
            
    query_string = '&'.join(query_params)
    
    response = client.post(f"/api/subcategories?{query_string}", json=test_params)
    response_json = response.json()
    assert response.status_code == 200
    assert isinstance(response_json, dict)
    assert "subcategory" in response_json


def test_list_subcategories_frequency_valid(client):
    
    response = client.post("/api/subcategories/frequency")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    

def test_list_subcategories_frequency_valid_with_params(client):
    
    test_params = {
        "categories": "World",
        "topics": "Ethiopia",
    }
    
    query_params = []
    for key, value in test_params.items():
        if isinstance(value, list):
            for item in value:
                query_params.append(f"{key}={item}")
        else:
            query_params.append(f"{key}={value}")
            
    query_string = '&'.join(query_params)
    
    response = client.post(f"/api/subcategories/frequency?{query_string}", json=test_params)
    response_json = response.json()
    assert response.status_code == 200
    assert isinstance(response_json, list)
    