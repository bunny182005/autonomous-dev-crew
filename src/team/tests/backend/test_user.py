# tests/backend/test_user.py

import pytest
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def db_session():
    # Mock the DB session and create a new UserService instance
    async with get_db() as session: 
        yield session


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user_service = UserService(db_session)
    new_user = UserCreate(username="testuser", password="password123")
    
    user = await user_service.create_user(new_user)
    assert user.username == "testuser"
    assert user.password_hash != "password123"  # Ensure password is hashed


@pytest.mark.asyncio
async def test_create_user_duplicate_username(db_session: AsyncSession):
    user_service = UserService(db_session)
    new_user = UserCreate(username="testuser", password="password123")
    
    await user_service.create_user(new_user)  # Create the first user
    
    with pytest.raises(Exception):  # Check for unique constraint violation
        await user_service.create_user(new_user)