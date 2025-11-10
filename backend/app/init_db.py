from app.database import Base, engine
from app import models

def init_db():
    print("Creating tables (if not exist)...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

if __name__ == "__main__":
    init_db()
