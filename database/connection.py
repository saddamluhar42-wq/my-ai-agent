from contextlib import contextmanager

import psycopg

from config import (
    DATABASE_TIMEOUT,
    DATABASE_URL,
)


class DatabaseError(Exception):
    """Raised when a database operation fails."""


def is_database_configured():
    return bool(DATABASE_URL)


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise DatabaseError(
            "DATABASE_URL is not configured."
        )

    connection = None

    try:
        connection = psycopg.connect(
            DATABASE_URL,
            connect_timeout=DATABASE_TIMEOUT,
        )

        yield connection

        connection.commit()

    except Exception as error:
        if connection:
            connection.rollback()

        raise DatabaseError(
            str(error)
        ) from error

    finally:
        if connection:
            connection.close()


def execute(
    query,
    params=None,
    fetch=None,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                params or (),
            )

            if fetch == "one":
                return cursor.fetchone()

            if fetch == "all":
                return cursor.fetchall()

            return None


def execute_many(
    query,
    params_list,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                query,
                params_list,
            )


def execute_script(
    statements,
):
    with get_connection() as connection:
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)


def test_connection():
    if not DATABASE_URL:
        return False, "DATABASE_URL is not configured."

    try:
        row = execute(
            "SELECT 1;",
            fetch="one",
        )

        if row and row[0] == 1:
            return True, "PostgreSQL connection successful."

        return False, "PostgreSQL returned an unexpected result."

    except Exception as error:
        return False, str(error)
