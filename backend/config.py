
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                    *****     Environment config     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

# NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
# NEWSDATA_BASE_URL = "https://newsdata.io/api/1/news"


print("NEWS_API_KEY =", NEWS_API_KEY)
# print("Loaded NewsData.io key:", NEWSDATA_API_KEY is not None)