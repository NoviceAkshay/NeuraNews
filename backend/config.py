
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                    *****     Environment config     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

print("NEWS_API_KEY =", NEWS_API_KEY)