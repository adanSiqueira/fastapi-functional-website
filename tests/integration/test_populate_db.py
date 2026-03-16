import pytest
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import delete, select, update

import models
from database import AsyncSessionLocal, engine
from image_utils import PROFILE_PICS_DIR
from main import app

from tests.fixtures.mock_data import MockData

POPULATE_IMAGES_DIR = Path("./tests/fixtures/populate_images")

mock_data = MockData()
USERS = mock_data.USERS
POSTS = mock_data.POSTS
POST_44 = mock_data.POST_44


async def clear_existing_data() -> None:
    if PROFILE_PICS_DIR.exists():
        for file in PROFILE_PICS_DIR.iterdir():
            if file.is_file() and file.name != ".gitkeep":
                file.unlink()

    async with AsyncSessionLocal() as db:
        await db.execute(delete(models.Post))
        await db.execute(delete(models.User))
        await db.commit()


async def update_post_dates() -> None:
    now = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Post).order_by(models.Post.id))
        posts = result.scalars().all()

        if not posts:
            return

        await db.execute(
            update(models.Post)
            .where(models.Post.id == posts[0].id)
            .values(date_posted=now - timedelta(days=90)),
        )

        for i, post in enumerate(posts[1:], start=1):
            days_ago = (len(posts) - i) * 1.5
            hours_offset = (i * 7) % 24
            post_date = now - timedelta(days=days_ago, hours=hours_offset)

            await db.execute(
                update(models.Post)
                .where(models.Post.id == post.id)
                .values(date_posted=post_date),
            )

        await db.commit()


@pytest.mark.asyncio
async def test_populate_database():
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:

        await clear_existing_data()

        users: list[dict] = []

        # -------------------
        # CREATE USERS
        # -------------------
        for user_data in USERS:
            response = await client.post(
                "/api/users",
                json={
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                },
            )

            assert response.status_code == 201
            user = response.json()

            response = await client.post(
                "/api/users/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )

            assert response.status_code == 200
            token = response.json()["access_token"]

            if image_name := user_data.get("image"):
                image_path = POPULATE_IMAGES_DIR / image_name

                if image_path.exists():
                    response = await client.patch(
                        f"/api/users/{user['id']}/picture",
                        files={
                            "file": (
                                image_name,
                                image_path.read_bytes(),
                                "image/png",
                            ),
                        },
                        headers={"Authorization": f"Bearer {token}"},
                    )

                    assert response.status_code == 200

            users.append(
                {"id": user["id"], "username": user["username"], "token": token}
            )

        assert len(users) == len(USERS)

        # -------------------
        # CREATE POSTS
        # -------------------

        response = await client.post(
            "/api/posts",
            json={"title": POST_44["title"], "content": POST_44["content"]},
            headers={"Authorization": f"Bearer {users[0]['token']}"},
        )

        assert response.status_code == 201

        for i, post_data in enumerate(reversed(POSTS)):
            user = users[i % len(users)]

            response = await client.post(
                "/api/posts",
                json={
                    "title": post_data["title"],
                    "content": post_data["content"],
                },
                headers={"Authorization": f"Bearer {user['token']}"},
            )

            assert response.status_code == 201

        # -------------------
        # UPDATE POST DATES
        # -------------------

        await update_post_dates()

        # -------------------
        # VALIDATE DATABASE
        # -------------------

        async with AsyncSessionLocal() as db:
            users_result = await db.execute(select(models.User))
            posts_result = await db.execute(select(models.Post))

            users_db = users_result.scalars().all()
            posts_db = posts_result.scalars().all()

        assert len(users_db) == len(USERS)
        assert len(posts_db) == len(POSTS) + 1

    await engine.dispose()