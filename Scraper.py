import requests
import os
import time

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
ACTOR_ID = "apify/google-maps-reviews-scraper"


def trigger_apify_scraper(url: str, limit: int = 30):
    run_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_API_TOKEN}"

    payload = {
        "startUrls": [{"url": url}],
        "maxReviews": 25,
        "language": "en"
    }

    res = requests.post(run_url, json=payload)
    res.raise_for_status()
    return res.json()["data"]["id"]


def fetch_reviews(run_id: str, fallback_url: str):
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"

    while True:
        status = requests.get(status_url).json()["data"]["status"]
        if status == "SUCCEEDED":
            break
        if status in ["FAILED", "ABORTED"]:
            raise Exception("Apify scraper failed")
        time.sleep(2)

    dataset_id = requests.get(status_url).json()["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    items = requests.get(dataset_url).json()

    reviews = [i["text"] for i in items if i.get("text")]
    business_name = items[0].get("title", "Business") if items else "Business"
    business_address = items[0].get("address", "")

    return reviews, business_name, business_address
