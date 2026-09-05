import psycopg

from app.auth.password import (
    hash_password,
    verify_password,
)
from app.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


PSYCOPG_CONNECTION = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def get_user_by_username(username: str) -> dict | None:
    """
    Find one user by username.
    """

    sql = """
        SELECT
            user_id,
            username,
            password_hash,
            role,
            is_active,
            created_at
        FROM app_user
        WHERE username = %s
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (username,))
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": row[4],
        "created_at": row[5],
    }


def get_user_by_id(user_id: int) -> dict | None:
    """
    Find one user by internal user ID.
    """

    sql = """
        SELECT
            user_id,
            username,
            password_hash,
            role,
            is_active,
            created_at
        FROM app_user
        WHERE user_id = %s
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()

    if row is None:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "password_hash": row[2],
        "role": row[3],
        "is_active": row[4],
        "created_at": row[5],
    }


def create_user(
    username: str,
    password: str,
    role: str = "user",
) -> dict:
    """
    Create a new application user.
    """

    if role not in ("admin", "user","manager"):
        raise ValueError("Invalid role.")

    password_hash = hash_password(password)

    sql = """
        INSERT INTO app_user (
            username,
            password_hash,
            role
        )
        VALUES (%s, %s, %s)
        RETURNING
            user_id,
            username,
            role,
            is_active,
            created_at
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    username,
                    password_hash,
                    role,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "is_active": row[3],
        "created_at": row[4],
    }


def authenticate_user(
    username: str,
    password: str,
) -> dict | None:
    """
    Verify username/password and return the user if valid.
    """

    user = get_user_by_username(username)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(
        password,
        user["password_hash"],
    ):
        return None

    return user


def list_users() -> list[dict]:
    """
    Return all application users.
    """

    sql = """
        SELECT
            user_id,
            username,
            role,
            is_active,
            created_at
        FROM app_user
        ORDER BY user_id
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "role": row[2],
            "is_active": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]

def update_user(
    user_id: int,
    username: str,
    role: str,
    is_active: bool,
) -> dict | None:
    """
    Update editable user properties.
    """

    if role not in ("admin", "manager", "user"):
        raise ValueError("Invalid role.")

    sql = """
        UPDATE app_user
        SET
            username = %s,
            role = %s,
            is_active = %s
        WHERE user_id = %s
        RETURNING
            user_id,
            username,
            role,
            is_active,
            created_at
    """

    with psycopg.connect(PSYCOPG_CONNECTION) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    username,
                    role,
                    is_active,
                    user_id,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    if row is None:
        return None

    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2],
        "is_active": row[3],
        "created_at": row[4],
    }
