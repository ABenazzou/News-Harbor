def test_list_filters_valid(client):
    
    response = client.get("/api/filters")
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, dict)
    assert "subcategories" in response_json
    assert "categories" in response_json
    assert "topics" in response_json
    assert "authors" in response_json
