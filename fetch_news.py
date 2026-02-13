import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load API key from .env
# load_dotenv()
# API_KEY = os.getenv("NEWS_API_KEY")

API_KEY = "364749be69d6482ab58547983ead1d80"

if not API_KEY:
    raise ValueError("API key not found. Make sure it's in your .env file.")

BASE_URL = "https://newsapi.org/v2/everything"

# Use keywords instead of categories
keywords = ["technology", "sports", "business", "science", "health", "entertainment"]

# Get articles from last 7 days
from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

all_articles = []
article_id = 1

for keyword in keywords:
    print(f"Fetching keyword: {keyword}")

    params = {
        "q": keyword,
        "from": from_date,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 100,
        "apiKey": API_KEY
    }

    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if data.get("status") != "ok":
        print("Error fetching data:", data)
        continue

    for article in data["articles"]:
        if not article.get("title") or not article.get("description"):
            continue

        cleaned_article = {
            "id": article_id,
            "title": article["title"].strip(),
            "description": article["description"].strip(),
            "source": article["source"]["name"],
            "publishedAt": article["publishedAt"],
            "keyword": keyword
        }

        all_articles.append(cleaned_article)
        article_id += 1

print(f"Total cleaned articles collected: {len(all_articles)}")

with open("articles.json", "w") as f:
    json.dump(all_articles, f, indent=2)

print("Saved articles to articles.json")