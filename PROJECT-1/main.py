from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from AI_Agent import agent

app = FastAPI(title="AI Blog Generator Agent")

class BlogRequest(BaseModel):
    business_url: str
    keyword: str
    tone: str
    style: str

class FinalBlogRequest(BaseModel):
    selected_title: str
    reviews_text: str
    keyword: str
    tone: str
    style: str
    hashtags: list[str]
    sentiment_summary: dict

@app.post("/generate-blog/")
async def generate_blog(req: BlogRequest):
    result = agent.observe({
        "business_url": req.business_url,
        "keyword": req.keyword,
        "tone": req.tone,
        "style": req.style
    })

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result

@app.post("/finalize-blog/")
async def finalize_blog(req: FinalBlogRequest):
    result = agent.generate_final_blog({
        "business_url": "",
        "keyword": req.keyword,
        "tone": req.tone,
        "style": req.style,
        "reviews_text": req.reviews_text,
        "hashtags": req.hashtags,
        "sentiment_summary": req.sentiment_summary
    }, req.selected_title)

    return result
