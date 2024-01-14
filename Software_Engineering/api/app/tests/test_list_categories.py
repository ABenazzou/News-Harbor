def test_list_categories_valid(client):
    
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    