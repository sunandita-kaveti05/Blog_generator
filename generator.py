import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.0-flash")


def build_reviews_text(cleaned_reviews):
    return "\n".join([f"- {r['text']}" for r in cleaned_reviews[:10]])


def get_blog_titles(reviews_text, keyword, tone, style):
    prompt = f"""
Generate 5 SEO-optimized blog titles.

Keyword: {keyword}
Tone: {tone}
Style: {style}

Customer Reviews:
{reviews_text}
"""

    response = model.generate_content(prompt)
    return [t.strip("-• ") for t in response.text.splitlines() if len(t.strip()) > 5]


def generate_blog(
    title,
    reviews_text,
    keyword,
    tone,
    style,
    business_name,
    business_address
):
    prompt = f"""
Write a blog titled "{title}"

Business Name: {business_name}
Address: {business_address}

Keyword: {keyword}
Tone: {tone}
Style: {style}

Use only the following real customer reviews:
{reviews_text}

Include:
- Meta description
- Introduction
- Body with insights
- Conclusion
"""

    response = model.generate_content(prompt)
    return response.text
