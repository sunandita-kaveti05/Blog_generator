import os
import time
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Load API Keys
APIFY_API_TOKEN="apify_api_lpFwuma6q5yIcH2sHBbH3wsT1bCHQQ4FrnOy"
TOGETHER_API_KEY="abe36463dd7166e654bed74bd30cfc76815ab61986279d0e63924b5d2c330128"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

# Sentiment analyzer
analyzer = SentimentIntensityAnalyzer()


# 🔧 Tool 1: Scrape reviews from Google Maps using Apify
def scrape_reviews(url: str, limit: int = 30):
    print("🔧 Tool: Scraping reviews...")
    apify_url = f"https://api.apify.com/v2/acts/compass~Google-Maps-Reviews-Scraper/runs?token={APIFY_API_TOKEN}"
    payload = {"startUrls": [{"url": url}], "maxReviews": limit}
    headers = {"Content-Type": "application/json"}

    res = requests.post(apify_url, json=payload, headers=headers)
    run_id = res.json()['data']['id']
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_API_TOKEN}"

    wait = 1
    while True:
        status = requests.get(status_url).json()['data']['status']
        if status in ['SUCCEEDED', 'FAILED', 'ABORTED']:
            break
        time.sleep(wait)
        wait = min(wait * 2, 8)

    if status != "SUCCEEDED":
        raise Exception(f"❌ Scraper failed: {status}")

    dataset_id = requests.get(status_url).json()['data']['defaultDatasetId']
    reviews_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?format=json"
    return requests.get(reviews_url).json()


# 🔧 Tool 2: Analyze sentiment of reviews
def analyze_reviews(reviews):
    print("🔧 Tool: Analyzing review sentiment...")
    def label(text):
        score = analyzer.polarity_scores(text)['compound']
        return "Positive" if score > 0.2 else "Negative" if score < -0.2 else "Neutral"

    cleaned = []
    for r in reviews:
        text = (r.get("text") or "").strip()
        if text.lower() not in ["none", ""]:
            cleaned.append({
                "text": text,
                "stars": r.get("stars", ""),
                "reviewer": r.get("reviewerName", "Anonymous"),
                "sentiment": label(text)
            })
    return cleaned


# 🔧 Tool 3: Build a block of cleaned review quotes
def build_review_block(cleaned_reviews):
    return "\n\n".join([
        f"⭐ {r['stars']} by {r['reviewer']} ({r['sentiment']}):\n{r['text']}" for r in cleaned_reviews
    ])


# 🔧 Tool 4: Summarize sentiment counts
def summarize_sentiments(cleaned_reviews):
    summary = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for r in cleaned_reviews:
        summary[r["sentiment"]] += 1
    return summary


# 🔧 Tool 5: Hashtag generator
def generate_hashtags(text, keyword=""):
    blob = TextBlob(text.lower())
    phrases = blob.noun_phrases
    freq = {}
    for p in phrases:
        p = p.strip().replace(" ", "")
        if len(p) > 2 and p.isalpha():
            freq[p] = freq.get(p, 0) + 1
    sorted_tags = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    tags = [f"#{w[0].capitalize()}" for w in sorted_tags[:5]]
    if keyword:
        keytag = f"#{keyword.replace(' ', '')}"
        if keytag not in tags:
            tags.insert(0, keytag)
    return tags + ["#CustomerReviews", "#RealExperience"]


# 🔧 Tool 6: Blog title suggestion (LLM call)
def generate_titles_llm(reviews_text, keyword, tone, style):
    print("🔧 Tool: Generating blog titles using LLaMA 3...")

    prompt = f"""
You are a creative blog title generator.

Keyword: {keyword}
Tone: {tone}
Style: {style}

Generate 5 catchy, SEO-optimized blog post titles using this customer review content:

{reviews_text}
"""

    payload = {
        "model": "meta-llama/Llama-3-70b-chat-hf",
        "messages": [
            {"role": "system", "content": "You are a helpful blog assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        result = response.json()
        print("🪵 Raw LLM Response:", result)  # Optional: remove in production

        raw = result['choices'][0]['message']['content']
        titles = []

        # Parse markdown/formatted or quoted titles
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            if any(line.startswith(str(i)) for i in range(1, 6)) or line.startswith("-") or "**" in line:
                # Try to extract between double quotes
                if '"' in line:
                    extracted = line.split('"')[1]
                elif "**" in line:
                    extracted = line.split("**")[1] if len(line.split("**")) > 1 else line
                else:
                    extracted = line.lstrip("-•*0123456789. ").strip()

                if 5 < len(extracted) < 120:
                    titles.append(extracted)

        if not titles:
            print("⚠️ No titles could be extracted from LLM response.")
        return titles

    except Exception as e:
        print("❌ LLM title generation error:", e)
        print("📄 Full response (if any):", response.text if 'response' in locals() else "No response")
        return []



# 🔧 Tool 7: Blog generator (LLM call)
def generate_blog_llm(title, reviews_text, keyword, tone, style):
    print("🔧 Tool: Generating full blog using LLaMA 3...")
    prompt = f"""
Write a blog titled "{title}" using real customer reviews.

Use the following:
- Keyword: {keyword}
- Tone: {tone}
- Style: {style}
- Structure: meta description, intro, body with review quotes, conclusion

Only use info from these reviews:
{reviews_text}
"""
    payload = {
        "model": "meta-llama/Llama-3-70b-chat-hf",
        "messages": [
            {"role": "system", "content": "You are a skilled blog writer."},
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(TOGETHER_API_URL, json=payload, headers=headers)
    return response.json()['choices'][0]['message']['content']
import requests

WINSTON_API_KEY = "Tuxyj8B5XRqLCrF1UeiuE8q8utv2yRXMxcVkMobca14b1a46"  # 🔒 Use your new token (not the exposed one)

def check_ai_score(blogtext):
    print("🔍 Checking AI Detection Score with Winston AI...")

    url = "https://api.gowinston.ai/api/v1/detect/ai"
    headers = {
        "Authorization": f"Bearer {WINSTON_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "content": blogtext
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"🪵 Status Code: {response.status_code}")
        print(f"🪵 Response Text: {response.text[:500]}")

        if response.status_code != 200:
            print("⚠️ Non-200 response received")
            return None

        result = response.json()

        if 'score' in result:
            score = result['score']  # Usually a float between 0 and 1
            explanation = result.get('explanation', 'No explanation provided')
            print(f"🤖 AI Probability: {score:.2f} — {explanation}")
            return score
        else:
            print("⚠️ Unexpected response format:", result)
            return None

    except Exception as e:
        print("❌ Exception occurred:", e)
        return None
