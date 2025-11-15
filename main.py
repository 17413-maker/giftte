# === BACKEND: main.py (v6.0) ===
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import re
import logging
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gifte-osint")

# === LIFESPAN ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Gifté+ OSINT Backend v6.0 — STARTING")
    yield
    logger.info("Gifté+ OSINT Backend — SHUTDOWN")

app = FastAPI(title="Gifté+ OSINT v6.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === CONFIG ===
ABSTRACT_PHONE_KEY = "521155e18b15415aadd705a035a57fd9"
ABSTRACT_EMAIL_KEY = "a714f117250d428aa7c475b6f44f3b83"
ABSTRACT_IP_KEY = "c60344fcdad24bec87d9dc674c3891ae"
TENAPI_AUTH = "Basic MTc0MTM6c2lnbWFib3lAMQ=="  # 17413:sigmaboy@1

# === MODELS ===
class OSINTRequest(BaseModel):
    phone: str
    email1: str
    email2: str
    instagram: Optional[str] = None

    @validator("phone")
    def validate_phone(cls, v):
        if not re.search(r"^\+?[\d\s\-\(\)]{10,}$", v):
            raise ValueError("Invalid phone format")
        return v

    @validator("email1", "email2")
    def validate_email(cls, v):
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email")
        return v

    @validator("instagram")
    def validate_instagram(cls, v):
        if v and not re.match(r"^[A-Za-z0-9._]{1,30}$", v):
            raise ValueError("Invalid Instagram username")
        return v

class OSINTResponse(BaseModel):
    phone: Dict
    email1: Dict
    email2: Dict
    ip: Dict
    instagram: Optional[Dict] = None
    gift_recommendation: str
    osint_score: int  # 0-100

# === HTTP CLIENTS ===
async def http_get(url: str) -> Dict:
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            r = await client.get(url)
            return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}", "raw": r.text}
        except Exception as e:
            logger.error(f"HTTP GET failed: {url} | {e}")
            return {"error": "Network timeout"}

async def tenapi_post(endpoint: str, body: Dict) -> Dict:
    async with httpx.AsyncClient(timeout=12.0) as client:
        try:
            r = await client.post(
                f"https://tenapi.net/api{endpoint}",
                headers={"Authorization": TENAPI_AUTH, "Content-Type": "application/json"},
                json=body
            )
            if not r.ok:
                return {"error": f"TenAPI {r.status_code}", "raw": r.text}
            data = r.json()
            return data.get("data", data) if "data" in data else data
        except Exception as e:
            logger.error(f"TenAPI failed: {endpoint} | {e}")
            return {"error": "TenAPI unreachable"}

# === LOOKUP FUNCTIONS ===
async def lookup_phone(phone: str) -> Dict:
    clean = re.sub(r"[^\d+]", "", phone)
    formatted = clean if clean.startswith("+") else f"+{clean}"
    url = f"https://phoneintelligence.abstractapi.com/v1/?api_key={ABSTRACT_PHONE_KEY}&phone={formatted}"
    return await http_get(url)

async def lookup_email(email: str) -> Dict:
    url = f"https://emailvalidation.abstractapi.com/v1/?api_key={ABSTRACT_EMAIL_KEY}&email={email}"
    return await http_get(url)

async def get_user_ip() -> str:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://api.ipify.org?format=json")
            return r.json().get("ip", "unknown")
    except:
        logger.warning("IP detection failed")
        return "unknown"

async def lookup_ip(ip: str) -> Dict:
    if ip == "unknown":
        return {"ip": "unknown", "error": "IP detection failed"}
    url = f"https://ip-intelligence.abstractapi.com/v1/?api_key={ABSTRACT_IP_KEY}&ip_address={ip}"
    return await http_get(url)

async def lookup_instagram(username: str) -> Dict:
    endpoints = [
        "/instagram/web_profile_info",
        "/instagram/followers",
        "/instagram/following",
        "/instagram/media"
    ]
    tasks = [tenapi_post(ep, {"username": username}) for ep in endpoints]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    profile = results[0] if not isinstance(results[0], Exception) else {"error": str(results[0])}
    followers = results[1] if not isinstance(results[1], Exception) else {"error": str(results[1])}
    following = results[2] if not isinstance(results[2], Exception) else {"error": str(results[2])}
    media = results[3] if not isinstance(results[3], Exception) else {"error": str(results[3])}

    return {"profile": profile, "followers": followers, "following": following, "media": media}

# === GIFT AI + OSINT SCORING ===
def generate_gift_and_score(ig_data: Dict) -> tuple[str, int]:
    if not ig_data or "error" in ig_data.get("profile", {}):
        return "Custom Gift Card", 30

    bio = str(ig_data.get("profile", {}).get("bio", "")).lower()
    captions = " ".join([m.get("caption", "") for m in ig_data.get("media", {}).get("data", [])]).lower()
    text = f"{bio} {captions}"
    follower_count = len(ig_data.get("followers", {}).get("data", []))

    gifts = []
    score = 50

    if "travel" in text: gifts.append("Travel Backpack"); score += 15
    if any(w in text for w in ["food", "chef", "cook"]): gifts.append("Gourmet Spice Set"); score += 12
    if any(w in text for w in ["gym", "fitness", "workout"]): gifts.append("Fitness Tracker"); score += 14
    if any(w in text for w in ["book", "read", "novel"]): gifts.append("Bestseller Bundle"); score += 10
    if follower_count > 50000: gifts.append("Luxury Watch"); score += 20
    elif follower_count > 10000: gifts.append("Premium Headphones"); score += 12

    gift = gifts[0] if gifts else "Personalized Mug"
    return gift, min(score, 100)

# === MAIN ENDPOINT ===
@app.post("/osint", response_model=OSINTResponse)
async def full_osint(req: OSINTRequest):
    logger.info(f"OSINT request: phone={req.phone}, emails={req.email1}/{req.email2}, ig={req.instagram}")

    user_ip = await get_user_ip()
    ip_data = await lookup_ip(user_ip)

    tasks = [
        lookup_phone(req.phone),
        lookup_email(req.email1),
        lookup_email(req.email2),
    ]
    if req.instagram:
        tasks.append(lookup_instagram(req.instagram))

    results = await asyncio.gather(*tasks)

    phone_data = results[0]
    email1_data = results[1]
    email2_data = results[2]
    ig_data = results[3] if req.instagram else None

    gift, score = generate_gift_and_score(ig_data)

    return OSINTResponse(
        phone=phone_data,
        email1=email1_data,
        email2=email2_data,
        ip={"address": user_ip, "data": ip_data},
        instagram=ig_data,
        gift_recommendation=gift,
        osint_score=score
    )

@app.get("/")
def root():
    return {
        "status": "Gifté+ OSINT v6.0 LIVE",
        "hibp": "DISABLED",
        "endpoints": ["/osint (POST)", "/docs"]
    }
