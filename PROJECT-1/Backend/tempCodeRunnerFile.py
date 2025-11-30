import requests
import time
import os
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Apify setup
API_TOKEN = 'apify_api_lpFwuma6q5yIcH2sHBbH3wsT1bCHQQ4FrnOy'
APIFY_URL = f'https://api.apify.com/v2/acts/compass~Google-Maps-Reviews-Scraper/runs?token={API_TOKEN}'

# Together AI setup
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "abe36463dd7166e654bed74bd30cfc76815ab61986279d0e63924b5d2c330128"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

analyzer = SentimentIntensityAnalyzer()

def get_user_inputs():
    business_url = input("Enter Google Maps business URL: ").strip()
    keyword = input("Enter keyword for blog: ").strip()
    tone = input("Enter desired tone (e.g., witty, formal): ").strip()
    style = input("Enter writing style (e.g., informal blog, corporate article): ").strip()
    try:
        review_limit = int(input("Enter number of reviews to analyze (max 50): ").strip())
        max_reviews = min(review_limit, 50)
    except ValueError:
        max_reviews = 20
    return business_url, keyword, tone, style, max_reviews

def trigger_apify_scraper(business_url, max_reviews):
    payload = {"startUrls": [{"url": business_url}], "maxReviews": max_reviews}
    headers = {"Content-Type": "application/json"}
    response = requests.post(APIFY_URL, json=payload, headers=headers, timeout=15)
    if not response.ok:
        raise Exception("❌ Failed to start Apify actor.", response.text)
    run_id = response.json()['data']['id']
    print(f"✅ Actor started. Run ID: {run_id}")

    run_status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"
    wait = 1
    while True:
        status_response = requests.get(run_status_url, timeout=10)
        status = status_response.json()['data']['status']
        print(f"🔄 Current status: {status}")
        if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
            break
        time.sleep(wait)
        wait = min(wait * 2, 8)

    if status != 'SUCCEEDED':
        raise Exception(f"❌ Actor run failed. Final status: {status}")

    dataset_id = status_response.json()['data']['defaultDatasetId']
    return f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"

def fetch_reviews(dataset_url):
    response = requests.get(dataset_url, timeout=15)
    if not response.ok:
        raise Exception("❌ Could not fetch reviews.", response.text)
    return response.json()

def analyze_reviews(reviews):
    def label(text):
        score = analyzer.polarity_scores(text)['compound']
        if score > 0.2: return "Positive"
        elif score < -0.2: return "Negative"
        else: return "Neutral"

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
        f"⭐ {r['stars']} by {r['reviewer']} ({r['sentiment']}):\n{r['text']}" for r in cleaned_reviews
    ])

def get_blog_titles(reviews_text, keyword, tone, style):
    prompt = f"""
You are an expert blog writer.
🔑 Keyword: {keyword}
🎯 Tone: {tone}
🖋️ Style: {style}
Suggest 5 blog post title ideas that are helpful, engaging, SEO-friendly, and human-like.
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
    response = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=20)
    if not response.ok:
        raise Exception("❌ Failed to fetch title suggestions.", response.text)
    return response.json()['choices'][0]['message']['content']

def generate_blog(selected_title, reviews_text, keyword, tone, style):
    prompt = f"""
You are a skilled, SEO-optimized, human-like blog writer.
🔑 Keyword: {keyword}
🎯 Tone: {tone}
🖋️ Style: {style}
📌 Blog Title: {selected_title}
Write a full blog post using the real reviews below.
Include introduction, body, and conclusion. Optimize for SEO, add meta description.
📃 Reviews:
{reviews_text}
Blog:
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
        raise Exception("❌ Failed to generate blog.", response.text)
    return response.json()['choices'][0]['message']['content']

def main():
    business_url, keyword, tone, style, max_reviews = get_user_inputs()
    dataset_url = trigger_apify_scraper(business_url, max_reviews)
    raw_reviews = fetch_reviews(dataset_url)
    cleaned_reviews = analyze_reviews(raw_reviews)
    sentiment_summary = summarize_sentiments(cleaned_reviews)
    reviews_text = build_reviews_text(cleaned_reviews)

    print("\n📊 Sentiment Summary:")
    for k, v in sentiment_summary.items():
        print(f"{k}: {v}")

    print("\n🧠 Fetching blog title suggestions from Together AI...")
    titles = get_blog_titles(reviews_text, keyword, tone, style)
    print("\n📚 Blog Title Suggestions:\n")
    print(titles)

    selected_title = input("\n✍️ Enter the number or title you want to write about: ").strip()
    print("\n🧠 Generating full blog from Together AI...")
    blog = generate_blog(selected_title, reviews_text, keyword, tone, style)
    print("\n📝 Final Blog Post:\n")
    print(blog)
    print("\n🔍 Check for AI-detection here: https://yourdomain.com/ai-check?text=PASTE_YOUR_BLOG")

if __name__ == "__main__":
    main()
