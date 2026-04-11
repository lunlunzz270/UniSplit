import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from the .env file.
# load_dotenv() will automatically locate the .env file in that same directory.
load_dotenv()

# Retrieve the database URL from environment variables.
# Fall back to a local SQLite file so the app can run without extra setup.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///unisplit.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
