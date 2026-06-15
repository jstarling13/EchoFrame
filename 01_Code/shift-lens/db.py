from models.base import SessionLocal, create_all_tables

def get_db():
    """Get a database session (for dependency injection in FastAPI)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database (create all tables)."""
    create_all_tables()
    print("Database tables created successfully.")
