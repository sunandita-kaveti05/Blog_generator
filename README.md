# Blog Generator - GenAI Project
Overview

The AI-Powered Blog Generator is a full-stack application that automatically converts Google Business Profile (Google Maps) reviews into high-quality, SEO-optimized blog posts.

It integrates:

Apify API for scraping Google Maps reviews

NLTK VADER for sentiment analysis

Google Gemini 2.0 Flash for AI text generation

FastAPI backend for orchestration

HTML, CSS, JavaScript frontend for UI

The system generates a complete blog containing:

SEO title

Meta description

600+ word article

Review-based hashtags

Sentiment breakdown

(As described in the Abstract and Implementation sections of the report 

MINIPROJECT_REPORT

)

✨ Features

🔍 Scrapes real customer reviews using the Apify API

😊 Performs sentiment analysis using VADER

✍️ Generates SEO blog content using Google Gemini 2.0 Flash

🌐 FastAPI Backend with REST endpoints

💻 Clean UI built using HTML, CSS, JS

🚀 Fully automated content pipeline from input → review scraping → sentiment → blog generation

⚠️ Handles invalid URLs, no reviews, API failures gracefully (Testing section 

MINIPROJECT_REPORT

)

🏗️ System Architecture

The workflow includes (as shown in the Architecture diagram page 13 

MINIPROJECT_REPORT

):

User Input (Google Maps URL + keyword)

Frontend → FastAPI request

Apify Scraper → Extract reviews

Sentiment Analysis using VADER

Gemini 2.0 Flash → Generate blog

Frontend displays results

🧩 Tech Stack
Component	Technology	Purpose
Backend	FastAPI	API orchestration
Frontend	HTML, CSS, JS	UI
Scraper	Apify API	Extract Google reviews
Sentiment Analysis	NLTK VADER	Review polarity analysis
Text Generation	Google Gemini 2.0 Flash	Blog writing
Middleware	CORS	Cross-origin requests

(as in Table 1.1, page 25 

MINIPROJECT_REPORT

)

🛠️ Installation
1️⃣ Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd your-repo

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Add your API keys (Apify, Gemini)

Create a .env file:

APIFY_TOKEN=your_token
GEMINI_API_KEY=your_key

4️⃣ Start FastAPI backend
uvicorn main:app --reload

5️⃣ Open frontend

Open index.html in your browser.

📡 API Endpoint
POST /generate_blog

Request format (from page 21-22 of report 

MINIPROJECT_REPORT

):

{
  "google_maps_url": "",
  "keyword": "",
  "tone": "",
  "style": ""
}


Response includes:

place_name

insights (positive, neutral, negative, avg_compound)

total_reviews

sample_reviews

blog

hashtags

🎯 Results

According to the Testing & Results section (pages 25–28 

MINIPROJECT_REPORT

):

Average response time: 8–12 seconds

Sentiment accuracy: ~90%

Blog coherence: 95% human-like

Frontend delay: <1s

Output screenshots (Swagger + UI) shown on pages 37–38.

🚧 Limitations

(from Table 1.5 on page 27 

MINIPROJECT_REPORT

)

VADER works best only on English text

Occasional Apify API delays

Gemini API quota limits

Repetitive phrasing if model runs in constrained mode

🚀 Future Enhancements

(as suggested on page 31 

MINIPROJECT_REPORT

)

Multi-language support

Database integration

Improved LLM controls

Enhanced UI (themes, download options)

Social media auto-posting

Asynchronous backend for faster workloads

🏁 Conclusion

This system proves how AI + NLP + automation can turn raw customer feedback into meaningful, marketing-ready blog content.
It removes the manual effort of scraping, analyzing, and writing — creating a scalable, reliable tool for businesses and creators.

👩‍💻 Author

K. Sunandita
B.Tech CSE
The Apollo University, Chittoor
