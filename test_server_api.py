import pytest
from httpx import AsyncClient
from server_api import app


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message":"Hello from Agroapi"}


@pytest.mark.anyio
async def test_response_ndvi():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/field-middle-ndvi?field_name=map25")
    assert response.status_code == 200
    assert response.json() == {"ndvi_data": {"middle_ndvi": 0.55}}

