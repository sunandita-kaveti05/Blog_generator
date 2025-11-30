# run_agent.py — Main entry for execution
from AI_Agent import agent

def main():
    print("🌐 Welcome to your AI Blog Agent!")
    print("----------------------------------")

    # Input from user
    business_url = input("🔗 Enter Google Maps business URL: ").strip()
    keyword = input("🔍 Enter blog keyword (e.g., Luxury stay): ").strip()
    tone = input("🎨 Enter blog tone (e.g., Friendly): ").strip()
    style = input("✍️ Enter blog style (e.g., Storytelling): ").strip()

    # Step 1: Run agent for reviews + titles
    result = agent.observe({
        "business_url": business_url,
        "keyword": keyword,
        "tone": tone,
        "style": style
    })

    if isinstance(result, dict) and "error" in result:
        print(result["error"])
        return

    titles = result.get("titles")
    if not titles:
        print("❌ No blog titles generated.")
        return

    # Show blog titles to the user
    print("\n🎯 Choose one of the following blog titles:")
    for idx, title in enumerate(titles):
        print(f"{idx + 1}. {title}")

    # Ask user to select one
    choice = input("\nEnter the number of your chosen title: ").strip()
    try:
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(titles)):
            raise ValueError
    except ValueError:
        print("⚠️ Invalid choice. Exiting.")
        return

    selected_title = titles[choice_idx]

    # Step 2: Generate blog using selected title
    result = agent.generate_final_blog({
        "business_url": business_url,
        "keyword": keyword,
        "tone": tone,
        "style": style,
        "reviews_text": result["reviews_text"],
        "hashtags": result["hashtags"],
        "sentiment_summary": result["sentiment_summary"]
    }, selected_title)

    # Show final output
    print("\n✅ Blog generation complete!")
    print("📝 Title:", result.get("title"))
    print("🏷️ Hashtags:", " ".join(result.get("hashtags", [])))
    print("📊 Sentiment Summary:", result.get("sentiment_summary"))
    print("\n📖 Blog Content:\n")
    print(result.get("final_blog"))
    print(f"\n🤖 AI Detection Score: {result.get('ai_score'):.2f} (0 = human, 1 = AI)") if result.get("ai_score") is not None else print("AI score not available.")
    print("🏷️ Hashtags:", " ".join(result.get("hashtags", [])))

if __name__ == "__main__":
    main()
