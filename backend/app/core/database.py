import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from the .env file.
# load_dotenv() will automatically locate the .env file in that same directory.
load_dotenv()

# Retrieve the database URL from environment variables
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Add a safety check to prevent silent errors if the environment variable fails to load
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not found. Please check your .env file!")

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()