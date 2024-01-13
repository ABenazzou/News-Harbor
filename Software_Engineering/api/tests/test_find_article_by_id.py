def test_find_article_by_id_valid(client):
    
    valid_id = "65a082ab58612f1cbe78306b"
    response = client.get(f"/articles/{valid_id}")
    assert response.status_code == 200
    assert response.json()["id"] == valid_id


def test_find_article_by_id_not_found(client):
    
    invalid_id = "65a082ab58612f1cbe78306c"
    response = client.get(f"/articles/{invalid_id}")
    assert response.status_code == 404


def test_find_article_by_invalid_id(client):
    
    invalid_id = "Invalid Object ID"
    response = client.get(f"/articles/{invalid_id}")
    assert response.status_code == 400
