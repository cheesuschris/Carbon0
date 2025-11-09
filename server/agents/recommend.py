from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
import json

load_dotenv()
SERP_API_KEY = os.getenv("SERPAPI_KEY")


def get_sustainable_alternatives(product_name: str) -> dict:
    query = f"{product_name} sustainable eco-friendly alternative"
    params = {
        "engine": "google_shopping",
        "q": query,
        "num": 5,
        "api_key": SERP_API_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    items = results.get("shopping_results", [])[:5]

    alternatives = []
    for item in items:
        alternatives.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "link": item.get("link"),
            "source": item.get("source"),
            "thumbnail": item.get("thumbnail"),
            "rating": item.get("rating"),
            "reviews": item.get("reviews")
        })

    if not alternatives:
        return {"error": "No sustainable alternatives found"}

    return {"alternatives": alternatives}

if __name__ == "__main__":
    product = "Legendary Whitetails Men's Flannel Shirt Long Sleeve Button Down 100% Cotton"
    print(get_sustainable_alternatives(product))

