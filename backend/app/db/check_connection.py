
from sqlalchemy import text

from app.db.session import engine


def check_database_connection() -> None:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"Database connection successful: {result.scalar()}")


if __name__ == "__main__":
    check_database_connection()