from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend fetches
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class Query(BaseModel):
    query: str

@app.get("/")
def root():
    return {"message": "Aditya OSINT API is running."}

@app.post("/search")
def search(query: Query):
    # Mock results for demo
    results = []
    if "@" in query.query:
        results.append({"platform": "Gmail", "url": f"https://mail.google.com/mail/u/0/#search/{query.query}"})
    if query.query.isdigit() or query.query.startswith("+"):
        results.append({"platform": "Phone Lookup", "url": f"https://www.truecaller.com/search/in/{query.query}"})
    # Add more platforms here
    return {"results": results}
