import pytest


@pytest.mark.asyncio
async def test_ui_pages_return_html(async_client):
    pages = ["/", "/register", "/dashboard"]
    for path in pages:
        response = await async_client.get(path)
        assert response.status_code == 200, f"{path} should return 200"
        assert "text/html" in response.headers.get("content-type", "")
        assert "/static/styles.css" in response.text, f"{path} should link stylesheet"


@pytest.mark.asyncio
async def test_static_stylesheet_is_served(async_client):
    response = await async_client.get("/static/styles.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")
    body = response.text
    assert ":root" in body
    assert ".password-field" in body
    assert ".card" in body
