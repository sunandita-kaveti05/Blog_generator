from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import requests
import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from urllib.parse import unquote
from textblob import TextBlob
import re

app = FastAPI()

# API keys
API_TOKEN = os.getenv("APIFY_API_TOKEN") or "apify_api_lpFwuma6q5yIcH2sHBbH3wsT1bCHQQ4FrnOy"
APIFY_URL = f'https://api.apify.com/v2/acts/compass~Google-Maps-Reviews-Scraper/runs?token={API_TOKEN}'
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "abe36463dd7166e654bed74bd30cfc76815ab61986279d0e63924b5d2c330128"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

analyzer = SentimentIntensityAnalyzer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SuggestTitlesRequest(BaseModel):
    url: str
    keyword: str
    tone: str
    style: str
    review_limit: int = 40
    user_email: EmailStr

class GenerateBlogRequest(BaseModel):
    selected_title: str
    keyword: str
    tone: str
    style: str
    user_email: EmailStr
    reviews_text: str
    business_name: str
    business_address: str

def extract_name_from_url(url: str) -> str:
    try:
        match = re.search(r"/place/([^/@]+)", url)
        if match:
            raw = match.group(1)
            name = unquote(raw).replace("+", " ").strip()
            return name
    except:
        pass
    return "this business"

def trigger_apify_scraper(business_url, max_reviews):
    payload = {"startUrls": [{"url": business_url}], "maxReviews": max_reviews}
    headers = {"Content-Type": "application/json"}
    response = requests.post(APIFY_URL, json=payload, headers=headers, timeout=15)
    if not response.ok:
        raise Exception("❌ Failed to start Apify actor.", response.text)
    run_id = response.json()['data']['id']
    run_status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"
    wait = 1
    while True:
        status_response = requests.get(run_status_url, timeout=10)
        status = status_response.json()['data']['status']
        if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
            break
        time.sleep(wait)
        wait = min(wait * 2, 8)
    if status != 'SUCCEEDED':
        raise Exception(f"❌ Actor run failed. Final status: {status}")
    dataset_id = status_response.json()['data']['defaultDatasetId']
    return f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"

def fetch_reviews(dataset_url, original_url):
    response = requests.get(dataset_url, timeout=15)
    if not response.ok:
        raise Exception("❌ Could not fetch reviews.", response.text)
    reviews = response.json()
    business_address = ""
    for r in reviews:
        if r.get("locationAddress"):
            business_address = r["locationAddress"].strip()
            break

    business_name = ""
    for r in reviews:
        if r.get("locationName") and r["locationName"].strip().lower() != "google user":
            business_name = r["locationName"].strip()
            break
    if not business_name:
        business_name = extract_name_from_url(original_url)
    return reviews, business_name, business_address

def analyze_reviews(reviews):
    def label(text):
        score = analyzer.polarity_scores(text)['compound']
        return "Positive" if score > 0.2 else "Negative" if score < -0.2 else "Neutral"
    cleaned = []
    for r in reviews:
        text = r.get("text")
        if text and text.strip().lower() not in ["none", ""]:
            cleaned.append({
                "text": text.strip(),
                "stars": r.get("stars"),
                "reviewer": r.get("reviewerName") or "Anonymous",
                "sentiment": label(text.strip())
            })
    return cleaned

def summarize_sentiments(cleaned_reviews):
    summary = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for r in cleaned_reviews:
        summary[r['sentiment']] += 1
    return summary

def build_reviews_text(cleaned_reviews):
    return "\n\n".join([
        f"\u2b50 {r['stars']} by {r['reviewer']} ({r['sentiment']}):\n{r['text']}" for r in cleaned_reviews
    ])

def generate_hashtags_from_reviews(reviews_text, keyword=None):
    blob = TextBlob(reviews_text.lower())
    noun_phrases = blob.noun_phrases

    freq = {}
    for phrase in noun_phrases:
        phrase = phrase.strip().replace(' ', '')
        if len(phrase) > 2 and phrase.isalpha():
            freq[phrase] = freq.get(phrase, 0) + 1

    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_phrases = [f"#{word[0].capitalize()}" for word in sorted_keywords[:5]]

    if keyword:
        tag = f"#{keyword.replace(' ', '')}"
        if tag not in top_phrases:
            top_phrases.insert(0, tag)

    base_tags = ["#CustomerReviews", "#RealExperience"]
    return top_phrases + base_tags

def get_blog_titles(reviews_text, keyword, tone, style):
    prompt = f"""
You are an expert blog writer.
🔑 Keyword: {keyword}
🎯 Tone: {tone}
🕋️ Style: {style}
Suggest 5 short, catchy, SEO-friendly blog post titles. Avoid explanations or extra text.
📃 Reviews:
{reviews_text}
"""
    payload = {
        "model": "meta-llama/Llama-3-70b-chat-hf",
        "messages": [
            {"role": "system", "content": "You are a helpful blog-writing assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
    if not response.ok:
        raise Exception("❌ Failed to fetch blog titles", response.text)
    raw = response.json()['choices'][0]['message']['content']
    lines = raw.strip().split("\n")

    titles = []
    for line in lines:
        line = line.strip()
        if not line or "title" in line.lower() or "related to" in line.lower():
            continue
        line = line.lstrip("-•*0123456789. ").strip('" ')
        if 5 < len(line) < 100:
            titles.append(line)
    return titles

def generate_blog(title, reviews_text, keyword, tone, style, business_name, business_address):
    prompt = f"""
You are a skilled, SEO-optimized, human-like blog writer.

📝 Task:
Write a compelling and complete blog post for **{business_name}**, using real customer reviews and based on the details below.

📍 Business Info:
- **Name**: {business_name}
- **Address**: {business_address}

🔑 Blog Requirements:
- Focus Keyword: **{keyword}**
- Tone: **{tone}**
- Style: **{style}**

🤩 Structure:
- A catchy **meta description** with keywords
- A strong **introduction** that introduces {business_name} and its address
- A short **overview/about section** describing the type of business and general experience
- A detailed **body section** using insights and quotes from real customer reviews
- A thoughtful **conclusion** that wraps up and encourages customers to visit or explore the business
- Use the keyword naturally throughout
- Ensure the writing feels natural, human, and engaging (not robotic)

📃 Real Google Reviews:
{reviews_text}

🌟 Goals:
- Make it SEO-optimized
- Write in a helpful, authentic, and friendly voice
- Avoid made-up info — use only what’s in reviews or provided fields
- Mention **{business_name}** and **{business_address}** naturally multiple times if relevant

Begin writing the blog below.
"""
    payload = {
        "model": "meta-llama/Llama-3-70b-chat-hf",
        "messages": [
            {"role": "system", "content": "You are a helpful blog-writing assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
    if not response.ok:
        raise Exception("❌ Failed to generate blog", response.text)
    return response.json()['choices'][0]['message']['content']

@app.get("/")
async def root():
    return {"message": "✅ API is running."}

@app.post("/suggest-titles")
async def suggest_titles(data: SuggestTitlesRequest):
    dataset_url = trigger_apify_scraper(data.url, min(data.review_limit, 50))
    raw_reviews, business_name, business_address = fetch_reviews(dataset_url, data.url)
    cleaned_reviews = analyze_reviews(raw_reviews)
    reviews_text = build_reviews_text(cleaned_reviews)
    titles = get_blog_titles(reviews_text, data.keyword, data.tone, data.style)
    summary = summarize_sentiments(cleaned_reviews)
    hashtags = generate_hashtags_from_reviews(reviews_text, data.keyword)
    return {
        "suggested_titles": titles,
        "reviews_text": reviews_text,
        "sentiment_summary": summary,
        "business_name": business_name,
        "business_address": business_address,
        "hashtags": hashtags
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
        data.business_address
    )
    address_to_use = data.business_address or "a convenient location"
    blog = blog.replace("[Business Name]", data.business_name)\
           .replace("[Address]", address_to_use)\
           .replace("this business", data.business_name)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {
        "blog": blog,
        "title": data.selected_title.strip(),
        "timestamp": timestamp,
        "ai_check_result": "Human-like"
    }
