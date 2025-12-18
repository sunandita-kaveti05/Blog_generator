from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_reviews(reviews):
    cleaned = []

    for text in reviews:
        score = analyzer.polarity_scores(text)["compound"]
        if score >= 0.05:
            sentiment = "Positive"
        elif score <= -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        cleaned.append({
            "text": text,
            "sentiment": sentiment
        })

    return cleaned


def summarize_sentiments(cleaned_reviews):
    summary = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for r in cleaned_reviews:
        summary[r["sentiment"]] += 1

    return summary
