import pytest
from httpx import AsyncClient

from tests.conftest import (
    auth_header, 
    create_test_user, 
    login_user
)

## Due to the transaction rollback set on conftest.py, the test DB
## starts empty, each test session.

@pytest.mark.anyio
async def test_get_posts_empty(client: AsyncClient):

    response = await client.get("/api/posts")    # Note: Pytest automatically get the client fixture from conftest.py
    assert response.status_code == 200

    data = response.json()
    assert data["posts"] == []
    assert data["total"] == 0
    assert data["has_more"] is False