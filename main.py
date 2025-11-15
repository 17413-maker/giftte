# === BACKEND: main.py (v9.3 — 500 ERROR FIXED) ===
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import re
import logging
from pydantic import BaseModel
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gifte")

app = FastAPI(title="Gifté+ v9.3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# === KEYS ===
NUMVERIFY_KEY = "02732386dc8873e2d6944b750e5903e9"
TENAPI_AUTH = "Basic MTc0MTM6c2lnbWFib3lAMQ=="
TRUECALLER_INSTALL_ID = "a1k07--YOUR_INSTALL_ID"

# === MODELS ===
class Input(BaseModel):
    email: str
    phone: str
    instagram: Optional[str] = None

class Output(BaseModel):
    debug_log: list
    email: Dict
    phone: Dict
    ip: Dict
    instagram: Dict
    truecaller: Dict
    ghunt_dorks: list
    gift: str
    score: int

# === HTTP HELPERS ===
async def get(url: str) -> Dict:
    async with httpx.AsyncClient(timeout=12) as c:
        try:
            r = await c.get(url)
            return {"status": r.status_code, "data": r.json() if r.ok else {"error": r.text}}
        except Exception as e:
            return {"status": "error", "data": str(e)}

async def post(url: str, json: Dict, headers: Dict) -> Dict:
    async with httpx.AsyncClient(timeout=12) as c:
        try:
            r = await c.post(url, json=json, headers=headers)
            return {"status": r.status_code, "data": r.json() if r.ok else {"error": r.text}}
        except Exception as e:
            return {"status": "error", "data": str(e)}

# === TOOLS ===
async def email_disify(email: str) -> Dict:
    return await get(f"https://disify.com/api/email/{email}")

async def email_osint_industries(email: str) -> Dict:
    return await get(f"https://osint.industries/api/email/{email}")

async def phone_numverify(phone: str) -> Dict:
    clean = re.sub(r"[^\d+]", "", phone)
    return await get(f"http://apilayer.net/api/validate?access_key={NUMVERIFY_KEY}&number={clean}&format=1")

async def phone_osint_industries(phone: str) -> Dict:
    clean = re.sub(r"[^\d+]", "", phone)
    return await get(f"https://osint.industries/api/phone/{clean}")

async def truecaller_lookup(phone: str) -> Dict:
    if not TRUECALLER_INSTALL_ID or "YOUR_INSTALL_ID" in TRUECALLER_INSTALL_ID:
        return {"error": "Truecaller ID not set"}
    clean = re.sub(r"[^\d+]", "", phone)
    url = "https://search5-noneu.truecaller.com/v2/search"
    params = {
        "q": clean,
        "countryCode": "IN",
        "type": 4,
        "locAddr": "",
        "placement": "SEARCHRESULTS,HISTORY,DETAILS"
    }
    headers = {
        "Authorization": f"Bearer {TRUECALLER_INSTALL_ID}",
        "User-Agent": "Truecaller/11.75.5"
    }
    full_url = f"{url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return await get(full_url)

# FIXED: SYNC FUNCTION
def ghunt_dorks(email: str) -> list:
    try:
        username, domain = email.split("@")
        return [
            f"from:{email}",
            f"to:{email}",
            f"site:{domain} {username}",
            f"inurl:{domain} {username}",
            f"\"{username}\" filetype:pdf",
            f"\"{email}\" -site:{domain}"
        ]
    except:
        return ["Invalid email"]

async def get_ip() -> str:
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get("https://api.ipify.org?format=json")
            return r.json().get("ip", "unknown")
    except:
        return "unknown"

async def ip_geo(ip: str) -> Dict:
    if ip == "unknown":
        return {"error": "IP detection failed"}
    return await get(f"http://ip-api.com/json/{ip}")

async def instagram_lookup(username: str) -> Dict:
    if not username:
        return {"error": "No username"}
    profile = await post(
        "https://tenapi.net/api/instagram/web_profile_info",
        json={"username": username},
        headers={"Authorization": TENAPI_AUTH, "Content-Type": "application/json"}
    )
    # FIXED: Handle 500 error
    data = profile.get("data", {})
    if profile.get("status") != 200 or not isinstance(data, dict):
        return {"username": username, "error": "TenAPI failed", "raw": profile}
    return {
        "username": username,
        "profile": data.get("data", {}) if "data" in data else data
    }

# === GIFT AI v3 — SAFE PARSING ===
def gift_ai(ig_data: Dict) -> tuple[str, int]:
    profile = ig_data.get("profile", {})
    if not isinstance(profile, dict):
        return "Custom Gift", 30

    bio = str(profile.get("biography") or profile.get("bio") or "").lower()
    captions = " ".join([
        m.get("caption", "") for m in profile.get("media", {}).get("data", [])
        if isinstance(m, dict)
    ]).lower()
    text = f"{bio} {captions}"

    traits = []
    score = 50

    if any(w in text for w in ["travel", "wander", "trip"]):
        traits.append("Travel Backpack"); score += 18
    if any(w in text for w in ["food", "cook", "chef"]):
        traits.append("Gourmet Set"); score += 15
    if any(w in text for w in ["gym", "fitness", "workout"]):
        traits.append("Fitness Tracker"); score += 16
    if any(w in text for w in ["book", "read", "novel"]):
        traits.append("Book Bundle"); score += 12

    follower_count = profile.get("follower_count", 0)
    if isinstance(follower_count, (int, float)):
        if follower_count > 50000:
            traits.append("Luxury Watch"); score += 20
        elif follower_count > 10000:
            traits.append("Smart Speaker"); score += 12

    gift = traits[0] if traits else "Personalized Mug"
    return gift, min(score, 100)

# === MAIN ENDPOINT ===
@app.post("/osint", response_model=Output)
async def osint(data: Input):
    debug = []
    debug.append(f"Input → email: {data.email}, phone: {data.phone}, ig: {data.instagram or 'auto'}")

    if "@" not in data.email:
        raise HTTPException(400, "Invalid email")
    if len(re.sub(r"[^\d+]", "", data.phone)) < 7:
        raise HTTPException(400, "Invalid phone")

    tasks = [
        email_disify(data.email),
        email_osint_industries(data.email),
        phone_numverify(data.phone),
        phone_osint_industries(data.phone),
        truecaller_lookup(data.phone),
        get_ip(),
        instagram_lookup(data.instagram or data.email.split("@")[0].lower())
    ]
    results = await asyncio.gather(*tasks)

    debug.append(f"All {len(results)} tasks completed")

    email_data = {"disify": results[0], "osint_industries": results[1]}
    phone_data = {"numverify": results[2], "osint_industries": results[3]}
    truecaller_data = results[4]
    user_ip = results[5]
    ip_data = await ip_geo(user_ip)
    ig_data = results[6]
    dorks = ghunt_dorks(data.email)  # SYNC
    gift, score = gift_ai(ig_data)

    return Output(
        debug_log=debug,
        email=email_data,
        phone=phone_data,
        ip={"address": user_ip, "geo": ip_data},
        instagram=ig_data,
        truecaller=truecaller_data,
        ghunt_dorks=dorks,
        gift=gift,
        score=score
    )

@app.get("/")
def root():
    return {"status": "Gifté+ v9.3 LIVE — 500 FIXED"}
