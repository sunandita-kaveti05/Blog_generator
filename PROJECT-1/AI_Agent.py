# AI_Agent.py — Converted to class-based ADK agent (no @step)
from google.adk.agents import Agent
from Tools import (
    scrape_reviews,
    analyze_reviews as analyze_reviews_tool,
    build_review_block,
    summarize_sentiments as summarize_tool,
    generate_hashtags,
    generate_titles_llm,
    generate_blog_llm,
    check_ai_score as detect_ai_score
)

class BlogAgent(Agent):
    def observe(self, observation):
        print("\n🤖 [Agent] Starting blog generation...")

        url = observation.get("business_url")
        keyword = observation.get("keyword")
        tone = observation.get("tone")
        style = observation.get("style")

        # Step 1: Scrape Reviews
        try:
            reviews = scrape_reviews(url)
        except Exception as e:
            return {"error": f"❌ Failed to scrape reviews: {e}"}

        if not reviews or len(reviews) < 5:
            return {"error": "⚠️ Not enough reviews to generate meaningful content."}

        # Step 2: Analyze Reviews
        cleaned = analyze_reviews_tool(reviews)
        review_text = build_review_block(cleaned)
        sentiment_summary = summarize_tool(cleaned)
        hashtags = generate_hashtags(review_text, keyword)

        # Step 3: Generate Titles
        titles = generate_titles_llm(review_text, keyword, tone, style)
        if not titles:
            return {"error": "❌ Failed to generate blog titles."}

        # Package partial result and title list for user selection
        return {
            "titles": titles,
            "cleaned_reviews": cleaned,
            "reviews_text": review_text,
            "sentiment_summary": sentiment_summary,
            "hashtags": hashtags
        }

    def generate_final_blog(self, observation, selected_title):
        print("\n🧠 [Agent] Finalizing blog...")

        blog = generate_blog_llm(
            selected_title,
            observation["reviews_text"],
            observation["keyword"],
            observation["tone"],
            observation["style"]
        )

        ai_score = detect_ai_score(blog)

        return {
            "title": selected_title,
            "hashtags": observation["hashtags"],
            "sentiment_summary": observation["sentiment_summary"],
            "final_blog": blog,
            "ai_score": ai_score
        }

# Create agent instance
agent = BlogAgent(name="BlogWriterAgent", description="A blogging agent using Google reviews")


