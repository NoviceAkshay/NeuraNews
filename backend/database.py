#
# # -----------------------------------------------------------------------------------------------------------------------------------------------------------
# #                                                     *****     Database     *****
# # -----------------------------------------------------------------------------------------------------------------------------------------------------------
#
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from dotenv import load_dotenv
# from pathlib import Path
# import os
# from urllib.parse import quote_plus
#
# # Load .env from project root
# env_path = Path(__file__).resolve().parent.parent / ".env"
# load_dotenv(dotenv_path=env_path)
#
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT")
# DB_NAME = os.getenv("DB_NAME")
#
# DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#
# print("DEBUG DATABASE_URL:", DATABASE_URL)
#
# engine = create_engine(
#     DATABASE_URL,
#     pool_pre_ping=True,   # avoid stale Supabase connections
#     pool_recycle=1800,    # recycle every 30 minutes
#     pool_size=5,
#     max_overflow=5,
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()
#
#


# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Database     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool  # ADD: for transaction pool (6543)
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus
from urllib.parse import urlparse  # ADD: to inspect port

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("DEBUG DATABASE_URL:", DATABASE_URL)

# Decide pooling strategy based on port/mode:
# - 6543 = transaction pool: let external pooler manage connections (NullPool)
# - 5432 = session pool: keep a small in-app pool to avoid exceeding server pool size
_port = int(DB_PORT) if DB_PORT and DB_PORT.isdigit() else None
use_transaction_pool = (_port == 6543)

if use_transaction_pool:
    # External pooler (PgBouncer/Supavisor) in transaction mode
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,        # don't hold connections in-app
        pool_pre_ping=True,        # validate before use
        connect_args={"sslmode": "require"},  # Supabase
    )
else:
    # Session mode: keep pool tiny so you don't hit MaxClients
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,               # keep small
        max_overflow=0,            # do not burst beyond pool_size
        connect_args={"sslmode": "require"},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Optional: safe session dependency for FastAPI
from sqlalchemy.orm import Session

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
