
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Database Tabel    *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------

from backend.database import engine, Base
from backend import models  # <-- Import models to register them!

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
