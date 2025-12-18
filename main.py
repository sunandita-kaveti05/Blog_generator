from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from Scraper import trigger_apify_scraper, fetch_reviews
from sentiment import analyze_reviews, summarize_sentiments
from generator import (
    build_reviews_text,
    get_blog_titles,
    generate_blog
)

app = FastAPI(title="AI Powered Blog Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "✅ API is running."}


class SuggestTitlesRequest(BaseModel):
    url: str
    keyword: str
    tone: str
    style: str
    review_limit: int = 30


class GenerateBlogRequest(BaseModel):
    selected_title: str
    reviews_text: str
    keyword: str
    tone: str
    style: str
    business_name: str
    business_address: str | None = None


@app.post("/suggest-titles")
async def suggest_titles(data: SuggestTitlesRequest):
    run_id = trigger_apify_scraper(data.url, min(data.review_limit, 50))
    raw_reviews, name, address = fetch_reviews(run_id, data.url)

    cleaned = analyze_reviews(raw_reviews)
    reviews_text = build_reviews_text(cleaned)

    titles = get_blog_titles(reviews_text, data.keyword, data.tone, data.style)
    summary = summarize_sentiments(cleaned)

    return {
        "suggested_titles": titles,
        "reviews_text": reviews_text,
        "sentiment_summary": summary,
        "business_name": name,
        "business_address": address
    }


@app.post("/generate-blog")
async def generate_blog_route(data: GenerateBlogRequest):
    blog = generate_blog(
        data.selected_title,
        data.reviews_text,
        data.keyword,
        data.tone,
        data.style,
        data.business_name,
        data.business_address or "a convenient location"
    )

    return {
        "title": data.selected_title,
        "blog": blog,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ai_check_result": "Human-like"
    }
