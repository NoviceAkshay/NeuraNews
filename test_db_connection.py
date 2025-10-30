
from backend.database import Base, engine
from backend.models import News, User

Base.metadata.create_all(bind=engine)
print("Tables created successfully in Supabase database!")
