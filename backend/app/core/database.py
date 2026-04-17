import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from the .env file.
# load_dotenv() will automatically locate the .env file in that same directory.
load_dotenv()

# Retrieve the database URL from environment variables.
# Fall back to the project-local SQLite file so every entrypoint shares the same DB.
DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "instance" / "unisplit.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


def _prepare_sqlite_storage(database_url: str) -> None:
    """Create the parent directory for local SQLite files if needed."""
    if not database_url.startswith("sqlite:"):
        return

    # Handle the common sqlite:///path/to/file.db form used by this project.
    if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        db_path = Path(database_url.replace("sqlite:///", "", 1))
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        return

    # Handle absolute sqlite:////path/to/file.db URLs as well.
    if database_url.startswith("sqlite:////"):
        db_path = Path("/" + database_url.replace("sqlite:////", "", 1).lstrip("/"))
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)


_prepare_sqlite_storage(SQLALCHEMY_DATABASE_URL)

# For debugging in CI: print the database type (obfuscate credentials)
db_info = SQLALCHEMY_DATABASE_URL.split("@")[-1] if "@" in SQLALCHEMY_DATABASE_URL else SQLALCHEMY_DATABASE_URL
print(f"DATABASE_CONNECTION | Info: Connecting to {db_info}")

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_compatibility():
    """Apply lightweight compatibility fixes for existing SQLite dev databases."""
    if engine.url.get_backend_name() != "sqlite":
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    def add_column_if_missing(conn, table: str, columns: set[str], column_sql: str, column_name: str):
        if table in tables and column_name not in columns:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))

    with engine.begin() as conn:
        if "users" in tables:
            user_columns = {col["name"] for col in inspector.get_columns("users")}
            if "full_name" not in user_columns and "name" in user_columns:
                conn.execute(text("ALTER TABLE users RENAME COLUMN name TO full_name"))
                user_columns = {col["name"] for col in inspect(engine).get_columns("users")}
            add_column_if_missing(conn, "users", user_columns, "created_at DATETIME", "created_at")
            add_column_if_missing(conn, "users", user_columns, "updated_at DATETIME", "updated_at")
            add_column_if_missing(conn, "users", user_columns, "is_active BOOLEAN DEFAULT 1", "is_active")
            add_column_if_missing(conn, "users", user_columns, "balance NUMERIC(10, 2) DEFAULT 0.00", "balance")

        if "groups" in tables:
            group_columns = {col["name"] for col in inspector.get_columns("groups")}
            add_column_if_missing(conn, "groups", group_columns, "created_at DATETIME", "created_at")
            add_column_if_missing(conn, "groups", group_columns, "updated_at DATETIME", "updated_at")

        if "group_members" in tables:
            member_columns = {col["name"] for col in inspector.get_columns("group_members")}
            add_column_if_missing(conn, "group_members", member_columns, "joined_at DATETIME", "joined_at")
            add_column_if_missing(conn, "group_members", member_columns, "role VARCHAR(50) DEFAULT 'MEMBER'", "role")

        if "expenses" in tables:
            expense_columns = {col["name"] for col in inspector.get_columns("expenses")}
            add_column_if_missing(conn, "expenses", expense_columns, "created_at DATETIME", "created_at")
            add_column_if_missing(conn, "expenses", expense_columns, "updated_at DATETIME", "updated_at")
            add_column_if_missing(conn, "expenses", expense_columns, "category VARCHAR(50)", "category")

        if "expense_participants" in tables:
            participant_columns = {col["name"] for col in inspector.get_columns("expense_participants")}
            add_column_if_missing(conn, "expense_participants", participant_columns, "is_settled BOOLEAN DEFAULT 0", "is_settled")

        if "settlements" in tables:
            settlement_columns = {col["name"] for col in inspector.get_columns("settlements")}
            add_column_if_missing(conn, "settlements", settlement_columns, "note TEXT", "note")
            add_column_if_missing(conn, "settlements", settlement_columns, "settled_at DATETIME", "settled_at")
