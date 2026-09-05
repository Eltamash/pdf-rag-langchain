from datetime import datetime, timedelta, timezone

import jwt

from app.config import (
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
)


def create_access_token(
    user_id: int,
    username: str,
    role: str,
) -> str:
    """
    Create a signed JWT access token.
    """

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Raises a PyJWT exception if:
    - signature is invalid
    - token is expired
    - token is malformed
    """

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

