from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Wait for the user to provide the Postgres connection string in the .env file.
# Supabase provides a Postgres connection string like: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
# For development/mock mode without credentials, we can fallback to SQLite
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql") else "sqlite:///./mock_database.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # check_same_thread is needed only for SQLite
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
