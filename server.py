#!/usr/bin/env python3
"""
Lanacord Grammys - Official Gala & Fake Betting Platform Server
Zero external dependencies, powered by Python 3 standard library.
Features:
- Dual execution: Standalone HTTP server (with SSE) + WSGI (for PythonAnywhere)
- Real-time Server-Sent Events (SSE) for instant cross-tab & cross-device updates
- Voter Betting Platform
- Admin Management & Results Control Center
- Dynamic Pari-Mutuel Odds Engine
- Persistent JSON State
- Passcode Security Gate for Admin controls
"""

import os
import sys
import json
import time
import uuid
import mimetypes
import queue
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_FILE = os.path.join(DATA_DIR, "grammys_state.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Thread-safe lock for state mutations
state_lock = threading.Lock()

# Global list of active SSE subscriber queues
sse_subscribers = []
sse_lock = threading.Lock()

def broadcast_event(event_type, payload=None):
    """Broadcast an SSE event to all connected clients."""
    with sse_lock:
        data_str = json.dumps({"type": event_type, "payload": payload, "timestamp": time.time()})
        msg = f"event: {event_type}\ndata: {data_str}\n\n"
        dead = []
        for q in sse_subscribers:
            try:
                q.put_nowait(msg)
            except Exception:
                dead.append(q)
        for d in dead:
            if d in sse_subscribers:
                sse_subscribers.remove(d)

INITIAL_CATEGORIES = [
    # Album Fan Categories
    {"section": "Album Fan Categories", "name": "Biggest BTD Fan", "description": "Who lives and breathes Born To Die, Lolita ribbons, and vintage red lipstick?"},
    {"section": "Album Fan Categories", "name": "Biggest Paradise Fan", "description": "Who embodies Ride, Gods & Monsters, and the wild side of Paradise?"},
    {"section": "Album Fan Categories", "name": "Biggest UV Fan", "description": "Crying tears of gold, leather jackets, Brooklyn Baby, and pure Ultraviolence."},
    {"section": "Album Fan Categories", "name": "Biggest LFL Fan", "description": "Stargirls, space aesthetics, and who has Lust for Life on 24/7 repeat?"},
    {"section": "Album Fan Categories", "name": "Biggest NFR Fan", "description": "Cinnamon Girl defenders, poetic souls, Norman Fucking Rockwell worshipers."},
    {"section": "Album Fan Categories", "name": "Biggest COTCC Fan", "description": "Chemtrails Over The Country Club, candlelit acoustics, and cottagecore royalty."},
    {"section": "Album Fan Categories", "name": "Biggest BB Fan", "description": "Blue Banisters tears, Arcadia hymns, and beautiful watercolor melancholia."},
    {"section": "Album Fan Categories", "name": "Biggest BB Hater", "description": "The certified Blue Banisters skeptic who won't stop complaining in general chat."},
    {"section": "Album Fan Categories", "name": "Biggest DYKTTATUOB Fan", "description": "Did you know that there's a tunnel under Ocean Blvd emotional damage enthusiast."},
    {"section": "Album Fan Categories", "name": "Biggest Lana Fan", "description": "The ultimate Lanita/Lanito. The grand deity of Lanacord Stan Twitter & Discord."},

    # Most Likely To Categories
    {"section": "Most Likely To Categories", "name": "Get Arrested", "description": "Most likely to end up in handcuffs on a Lana concert livestream."},
    {"section": "Most Likely To Categories", "name": "Burn a House Down", "description": "High drama, volatile energy, and arson-worthy aesthetics."},
    {"section": "Most Likely To Categories", "name": "Fake a Death", "description": "Going off the grid dramatic-style just to see who writes condolences."},
    {"section": "Most Likely To Categories", "name": "Be in a Cult", "description": "Would drink the kool-aid if the cult leader quotes Salvatore lyrics."},
    {"section": "Most Likely To Categories", "name": "Get Banned", "description": "Constantly walking on thin ice with the Lanacord mods and automod."},
    {"section": "Most Likely To Categories", "name": "Meet Lana", "description": "Manifesting a Waffle House run-in or VIP backstage encounter."},
    {"section": "Most Likely To Categories", "name": "Become Famous", "description": "Destined for viral TikTok fame or indie darling stardom."},
    {"section": "Most Likely To Categories", "name": "Become Rich", "description": "Either dropshipping vinyl records or manifesting millions."},
    {"section": "Most Likely To Categories", "name": "Become President", "description": "Campaign slogan: 'God bless America and all the beautiful women in it'."},

    # Best/Most/Favorite Categories
    {"section": "Best/Most/Favorite Categories", "name": "Best Music Taste", "description": "Their Spotify blend and Last.fm stats are simply immaculate."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Merch", "description": "Owns rare unreleased vinyl, vintage tour tees, and the Lana lighters."},
    {"section": "Best/Most/Favorite Categories", "name": "Most Chronically Online", "description": "Never leaves Discord voice chat or #general for more than 4 minutes."},
    {"section": "Best/Most/Favorite Categories", "name": "Funniest Member", "description": "Supplies the server with top-tier Lana memes, reaction gifs, and copypastas."},
    {"section": "Best/Most/Favorite Categories", "name": "Messiest Member", "description": "Spills all the tea, starts server civil wars, and leaves popcorn behind."},
    {"section": "Best/Most/Favorite Categories", "name": "Most Active", "description": "Top of the MEE6/Arcane leaderboard every single week without fail."},
    {"section": "Best/Most/Favorite Categories", "name": "Most Helpful", "description": "Always linking vinyl restocks, answering questions, and welcoming newcomers."},
    {"section": "Best/Most/Favorite Categories", "name": "Most Dramatic", "description": "Writes 5-paragraph dissertations when Lana delays an album by 2 days."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Profile Picture", "description": "PFP game is always aesthetic, high-res, and beautifully curated."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Layout", "description": "Their Discord profile bio, banners, badges, and colors are peak art."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Username", "description": "The most iconic, creative, or unhinged handle in Lanacord history."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Duo/Group", "description": "The inseparable dynamic duo or chaotic group chat of the server."},
    {"section": "Best/Most/Favorite Categories", "name": "Best Red Carpet Outfit", "description": "Serving the best gala looks, met-gala tier glamour, or camp fits."},
    {"section": "Best/Most/Favorite Categories", "name": "Favorite Member", "description": "The people's princess of Lanacord. Loved by everyone unanimously."}
]

DEFAULT_MEMBER_POOL = [
    {"name": "cinnamon_girl", "avatar": "cherry"},
    {"name": "venice_bitch", "avatar": "wave"},
    {"name": "ultraviolence_slut", "avatar": "lipstick"},
    {"name": "cherry_blossom", "avatar": "flower"},
    {"name": "norman_stan", "avatar": "sailor"},
    {"name": "brooklyn_baby", "avatar": "sunglasses"},
    {"name": "diet_mtn_dew", "avatar": "can"},
    {"name": "salvatore_wine", "avatar": "wine"},
    {"name": "lanita_del_rey", "avatar": "crown"},
    {"name": "waffle_house_waitress", "avatar": "coffee"},
    {"name": "ocean_blvd_ghost", "avatar": "ribbon"},
    {"name": "radio_star", "avatar": "mic"},
    {"name": "born_to_die_hard", "avatar": "rose"},
    {"name": "tupelo_honey", "avatar": "sparkles"}
]

def generate_default_state():
    categories = []
    pool_len = len(DEFAULT_MEMBER_POOL)
    for idx, cat_def in enumerate(INITIAL_CATEGORIES):
        cat_id = f"cat_{idx+1}_{cat_def['name'].lower().replace(' ', '_').replace('/', '_')}"
        nominees = []
        nom_count = 3 if idx % 2 == 0 else 4
        for n_offset in range(nom_count):
            member = DEFAULT_MEMBER_POOL[(idx * 2 + n_offset) % pool_len]
            nominees.append({
                "id": f"nom_{uuid.uuid4().hex[:8]}",
                "name": member["name"],
                "avatar": member["avatar"]
            })
        
        categories.append({
            "id": cat_id,
            "section": cat_def["section"],
            "name": cat_def["name"],
            "description": cat_def["description"],
            "nominees": nominees,
            "winnerId": None,
            "isLocked": False
        })
    
    default_pwd = os.environ.get("ADMIN_PASSWORD", "lanacord2026")
    return {
        "categories": categories,
        "users": {
            "demo_voter": {
                "id": "demo_voter",
                "username": "LanacordVIP",
                "balance": 2000,
                "createdAt": time.time()
            }
        },
        "bets": [],
        "activity": [
            {
                "id": "act_init",
                "text": "The 2026 Lanacord Grammys prediction pools are officially open.",
                "timestamp": time.time()
            }
        ],
        "meta": {
            "currencyName": "Points",
            "currencySymbol": "pts",
            "adminPassword": default_pwd,
            "version": "1.0.0"
        }
    }

def load_state():
    default_pwd = os.environ.get("ADMIN_PASSWORD", "lanacord2026")
    if not os.path.exists(DB_FILE):
        state = generate_default_state()
        state.setdefault("meta", {})["adminPassword"] = default_pwd
        save_state(state)
        return state
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            state.setdefault("meta", {})
            if "adminPassword" not in state["meta"]:
                state["meta"]["adminPassword"] = default_pwd
                save_state(state)
            return state
    except Exception as e:
        print(f"Error loading state: {e}. Reverting to default.")
        state = generate_default_state()
        state.setdefault("meta", {})["adminPassword"] = default_pwd
        save_state(state)
        return state

def save_state(state):
    try:
        temp_file = DB_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DB_FILE)
    except Exception as e:
        print(f"Error saving state: {e}")

# In-memory working copy
app_state = load_state()

def calculate_category_odds(category_id, state):
    category = next((c for c in state["categories"] if c["id"] == category_id), None)
    if not category:
        return {}
    
    nominees = category.get("nominees", [])
    if not nominees:
        return {}
    
    cat_bets = [b for b in state["bets"] if b["categoryId"] == category_id]
    
    nominee_pools = {n["id"]: 0 for n in nominees}
    nominee_counts = {n["id"]: 0 for n in nominees}
    for b in cat_bets:
        n_id = b["nomineeId"]
        if n_id in nominee_pools:
            nominee_pools[n_id] += b["amount"]
            nominee_counts[n_id] += 1
            
    total_pool = sum(nominee_pools.values())
    n_count = len(nominees)
    
    # Virtual liquidity for smooth odds calculation
    k_liquidity = max(300, n_count * 100)
    adjusted_total = total_pool + k_liquidity
    
    results = {}
    for n in nominees:
        nid = n["id"]
        pool = nominee_pools[nid]
        count = nominee_counts[nid]
        adjusted_pool = pool + (k_liquidity / n_count)
        share = adjusted_pool / adjusted_total
        
        decimal_odds = round(min(30.0, max(1.10, 1.0 / share)), 2)
        real_share = round((pool / total_pool * 100) if total_pool > 0 else (100.0 / n_count), 1)
        
        results[nid] = {
            "odds": decimal_odds,
            "pool": pool,
            "betCount": count,
            "sharePercentage": real_share
        }
    return results

def get_public_state_data(user_id=None):
    with state_lock:
        enriched_categories = []
        for cat in app_state["categories"]:
            odds_map = calculate_category_odds(cat["id"], app_state)
            cat_copy = dict(cat)
            cat_copy["odds"] = odds_map
            cat_bets = [b for b in app_state["bets"] if b["categoryId"] == cat["id"]]
            cat_copy["totalPool"] = sum(b["amount"] for b in cat_bets)
            cat_copy["totalBets"] = len(cat_bets)
            enriched_categories.append(cat_copy)
        
        user_stats = {}
        for uid, u in app_state["users"].items():
            user_stats[uid] = {
                "id": uid,
                "username": u["username"],
                "balance": u["balance"],
                "totalWon": 0,
                "betsPlaced": 0
            }
        
        for b in app_state["bets"]:
            uid = b["userId"]
            if uid in user_stats:
                user_stats[uid]["betsPlaced"] += 1
                if b.get("status") == "won":
                    user_stats[uid]["totalWon"] += b.get("payoutReceived", 0)
        
        leaderboard = sorted(user_stats.values(), key=lambda x: (x["balance"] + x["totalWon"]), reverse=True)[:15]
        
        user_bets = []
        current_user = None
        if user_id and user_id in app_state["users"]:
            current_user = app_state["users"][user_id]
            user_bets = [b for b in app_state["bets"] if b["userId"] == user_id]
            user_bets.sort(key=lambda x: x["timestamp"], reverse=True)
            
        total_bets_count = len(app_state["bets"])
        total_volume = sum(b["amount"] for b in app_state["bets"])
        total_categories = len(app_state["categories"])
        total_nominees = sum(len(c.get("nominees", [])) for c in app_state["categories"])

        return {
            "categories": enriched_categories,
            "activity": app_state["activity"][-25:],
            "leaderboard": leaderboard,
            "currentUser": current_user,
            "userBets": user_bets,
            "stats": {
                "totalCategories": total_categories,
                "totalNominees": total_nominees,
                "totalBets": total_bets_count,
                "totalVolume": total_volume,
                "activeVoters": len(app_state["users"])
            },
            "meta": {k: v for k, v in app_state.get("meta", {}).items() if k != "adminPassword"}
        }

# ==============================================================================
# UNIFIED REQUEST DISPATCHER (Used by both Standalone Server and WSGI/PythonAnywhere)
# ==============================================================================
def handle_request(method, path, query=None, headers=None, body=None):
    if query is None: query = {}
    if headers is None: headers = {}
    if body is None: body = {}

    h_lower = {k.lower(): v for k, v in headers.items()}

    def json_resp(data, status=200):
        body_bytes = json.dumps(data).encode("utf-8")
        res_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body_bytes)),
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Admin-Password"
        }
        return status, res_headers, body_bytes

    def file_resp(filepath, content_type=None):
        if not os.path.exists(filepath):
            return 404, {"Content-Type": "text/plain"}, b"404 Not Found"
        if not content_type:
            content_type, _ = mimetypes.guess_type(filepath)
            if not content_type:
                content_type = "application/octet-stream"
        with open(filepath, "rb") as f:
            c = f.read()
        return 200, {
            "Content-Type": content_type,
            "Content-Length": str(len(c)),
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*"
        }, c

    if method == "OPTIONS":
        return 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Admin-Password"
        }, b""

    if method == "GET":
        if path in ("/", "/voter", "/voter/"):
            return file_resp(os.path.join(STATIC_DIR, "voter.html"), "text/html; charset=utf-8")
        elif path in ("/admin", "/admin/"):
            return file_resp(os.path.join(STATIC_DIR, "admin.html"), "text/html; charset=utf-8")
        elif path == "/api/state":
            uid = query.get("userId", [None])[0]
            data = get_public_state_data(uid)
            return json_resp(data)
        elif path == "/api/events":
            return 200, {"Content-Type": "text/plain"}, b": ping\n\n"
        elif path.startswith("/static/"):
            rel = path[len("/static/"):]
            fpath = os.path.join(STATIC_DIR, rel)
            return file_resp(fpath)
        else:
            candidate = os.path.join(STATIC_DIR, path.lstrip("/"))
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return file_resp(candidate)
            return file_resp(os.path.join(STATIC_DIR, "voter.html"), "text/html; charset=utf-8")

    elif method == "POST":
        # Admin auth check
        if path.startswith("/api/admin/") and path != "/api/admin/verify":
            admin_pwd = h_lower.get("x-admin-password") or (body.get("adminPassword") if isinstance(body, dict) else None)
            expected_pwd = app_state.get("meta", {}).get("adminPassword", "lanacord2026")
            if not admin_pwd or admin_pwd != expected_pwd:
                return json_resp({"error": "Unauthorized: Invalid Admin Passcode", "success": False}, 401)

        # ---------------- USER: LOGIN ----------------
        if path == "/api/user/login":
            username = body.get("username", "").strip()
            if not username:
                return json_resp({"error": "Username cannot be empty", "success": False}, 400)
            
            with state_lock:
                existing_user = None
                for uid, u in app_state["users"].items():
                    if u["username"].lower() == username.lower():
                        existing_user = u
                        break
                
                if not existing_user:
                    uid = f"user_{uuid.uuid4().hex[:8]}"
                    existing_user = {
                        "id": uid,
                        "username": username,
                        "balance": 1000,
                        "createdAt": time.time()
                    }
                    app_state["users"][uid] = existing_user
                    save_state(app_state)
                    broadcast_event("USER_JOINED", {"user": existing_user})

            return json_resp({"success": True, "user": existing_user})

        # ---------------- USER: CLAIM ----------------
        elif path == "/api/user/claim":
            user_id = body.get("userId")
            with state_lock:
                if user_id not in app_state["users"]:
                    return json_resp({"error": "User not found", "success": False}, 404)
                user = app_state["users"][user_id]
                user["balance"] += 250
                save_state(app_state)
                broadcast_event("BALANCE_UPDATED", {"userId": user_id, "newBalance": user["balance"]})

            return json_resp({"success": True, "balance": user["balance"]})

        # ---------------- USER: PLACE BET ----------------
        elif path == "/api/bet":
            user_id = body.get("userId")
            category_id = body.get("categoryId")
            nominee_id = body.get("nomineeId")
            amount = body.get("amount")

            try:
                amount = int(amount)
            except (ValueError, TypeError):
                return json_resp({"error": "Invalid bet amount", "success": False}, 400)

            if amount <= 0:
                return json_resp({"error": "Bet amount must be greater than 0", "success": False}, 400)

            with state_lock:
                if user_id not in app_state["users"]:
                    return json_resp({"error": "User not found. Please log in first.", "success": False}, 400)
                
                user = app_state["users"][user_id]
                if user["balance"] < amount:
                    return json_resp({"error": f"Insufficient balance. You have {user['balance']} pts available.", "success": False}, 400)

                category = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not category:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                if category.get("isLocked") or category.get("winnerId"):
                    return json_resp({"error": "Betting for this category is currently locked or concluded.", "success": False}, 400)

                nominee = next((n for n in category.get("nominees", []) if n["id"] == nominee_id), None)
                if not nominee:
                    return json_resp({"error": "Nominee not found in this category", "success": False}, 404)

                odds_map = calculate_category_odds(category_id, app_state)
                current_odds = odds_map.get(nominee_id, {}).get("odds", 2.0)
                potential_payout = int(round(amount * current_odds))

                user["balance"] -= amount
                bet_id = f"bet_{uuid.uuid4().hex[:8]}"
                new_bet = {
                    "id": bet_id,
                    "userId": user_id,
                    "username": user["username"],
                    "categoryId": category_id,
                    "categoryName": category["name"],
                    "nomineeId": nominee_id,
                    "nomineeName": nominee["name"],
                    "amount": amount,
                    "oddsAtBet": current_odds,
                    "potentialPayout": potential_payout,
                    "status": "pending",
                    "timestamp": time.time()
                }
                app_state["bets"].append(new_bet)

                activity_item = {
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"@{user['username']} staked {amount} pts on @{nominee['name']} for '{category['name']}'",
                    "timestamp": time.time()
                }
                app_state["activity"].append(activity_item)
                if len(app_state["activity"]) > 50:
                    app_state["activity"].pop(0)

                save_state(app_state)
                broadcast_event("BET_PLACED", {
                    "bet": new_bet,
                    "activity": activity_item,
                    "categoryId": category_id
                })

            return json_resp({"success": True, "bet": new_bet, "newBalance": user["balance"]})

        # ---------------- ADMIN: VERIFY PASSCODE ----------------
        elif path == "/api/admin/verify":
            pwd = body.get("password", "")
            expected_pwd = app_state.get("meta", {}).get("adminPassword", "lanacord2026")
            if pwd == expected_pwd:
                return json_resp({"success": True})
            return json_resp({"error": "Invalid admin passcode", "success": False}, 401)

        # ---------------- ADMIN: CHANGE PASSCODE ----------------
        elif path == "/api/admin/change-password":
            new_pwd = body.get("newPassword", "").strip()
            if not new_pwd or len(new_pwd) < 4:
                return json_resp({"error": "New passcode must be at least 4 characters", "success": False}, 400)
            with state_lock:
                app_state["meta"]["adminPassword"] = new_pwd
                save_state(app_state)
            return json_resp({"success": True})

        # ---------------- ADMIN: CATEGORY ADD ----------------
        elif path == "/api/admin/category/add":
            name = body.get("name", "").strip()
            section = body.get("section", "Album Fan Categories").strip()
            description = body.get("description", "").strip()

            if not name:
                return json_resp({"error": "Category name is required", "success": False}, 400)

            with state_lock:
                cat_id = f"cat_{int(time.time())}_{name.lower().replace(' ', '_').replace('/', '_')}"
                new_cat = {
                    "id": cat_id,
                    "name": name,
                    "section": section,
                    "description": description or f"Lanacord Grammys category: {name}",
                    "nominees": [],
                    "winnerId": None,
                    "isLocked": False
                }
                app_state["categories"].append(new_cat)
                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"New category added: '{name}' in {section}.",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("CATEGORY_ADDED", {"category": new_cat})

            return json_resp({"success": True, "category": new_cat})

        # ---------------- ADMIN: CATEGORY DELETE ----------------
        elif path == "/api/admin/category/delete":
            category_id = body.get("categoryId")
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                app_state["categories"] = [c for c in app_state["categories"] if c["id"] != category_id]
                refunded_count = 0
                for b in app_state["bets"]:
                    if b["categoryId"] == category_id and b.get("status") == "pending":
                        uid = b["userId"]
                        if uid in app_state["users"]:
                            app_state["users"][uid]["balance"] += b["amount"]
                            refunded_count += 1
                        b["status"] = "refunded"

                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"Category '{cat['name']}' was removed ({refunded_count} stakes refunded).",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("CATEGORY_DELETED", {"categoryId": category_id})

            return json_resp({"success": True})

        # ---------------- ADMIN: CATEGORY EDIT ----------------
        elif path == "/api/admin/category/edit":
            category_id = body.get("categoryId")
            name = body.get("name", "").strip()
            section = body.get("section", "").strip()
            description = body.get("description", "").strip()

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                if name: cat["name"] = name
                if section: cat["section"] = section
                if description: cat["description"] = description
                save_state(app_state)
                broadcast_event("CATEGORY_EDITED", {"category": cat})

            return json_resp({"success": True, "category": cat})

        # ---------------- ADMIN: CATEGORY LOCK ----------------
        elif path == "/api/admin/category/lock":
            category_id = body.get("categoryId")
            locked = bool(body.get("isLocked", True))

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                cat["isLocked"] = locked
                save_state(app_state)
                broadcast_event("CATEGORY_LOCKED", {"categoryId": category_id, "isLocked": locked})

            return json_resp({"success": True, "isLocked": locked})

        # ---------------- ADMIN: NOMINEE ADD ----------------
        elif path == "/api/admin/nominee/add":
            category_id = body.get("categoryId")
            name = body.get("name", "").strip()
            avatar = body.get("avatar", "cherry").strip()

            if not name:
                return json_resp({"error": "Nominee member name is required", "success": False}, 400)

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                if any(n["name"].lower() == name.lower() for n in cat.get("nominees", [])):
                    return json_resp({"error": f"Nominee '{name}' is already in this category.", "success": False}, 400)

                new_nominee = {"id": f"nom_{uuid.uuid4().hex[:8]}", "name": name, "avatar": avatar}
                cat.setdefault("nominees", []).append(new_nominee)
                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"Candidate registered: @{name} in '{cat['name']}'.",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("NOMINEE_ADDED", {"categoryId": category_id, "nominee": new_nominee})

            return json_resp({"success": True, "nominee": new_nominee})

        # ---------------- ADMIN: NOMINEE DELETE ----------------
        elif path == "/api/admin/nominee/delete":
            category_id = body.get("categoryId")
            nominee_id = body.get("nomineeId")

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                nominee = next((n for n in cat.get("nominees", []) if n["id"] != nominee_id), None)
                target_nom = next((n for n in cat.get("nominees", []) if n["id"] == nominee_id), None)
                cat["nominees"] = [n for n in cat.get("nominees", []) if n["id"] != nominee_id]

                refunded_count = 0
                for b in app_state["bets"]:
                    if b["categoryId"] == category_id and b["nomineeId"] == nominee_id and b.get("status") == "pending":
                        uid = b["userId"]
                        if uid in app_state["users"]:
                            app_state["users"][uid]["balance"] += b["amount"]
                            refunded_count += 1
                        b["status"] = "refunded"

                if target_nom:
                    app_state["activity"].append({
                        "id": f"act_{uuid.uuid4().hex[:6]}",
                        "text": f"Candidate @{target_nom['name']} removed from '{cat['name']}' ({refunded_count} stakes refunded).",
                        "timestamp": time.time()
                    })

                save_state(app_state)
                broadcast_event("NOMINEE_DELETED", {"categoryId": category_id, "nomineeId": nominee_id})

            return json_resp({"success": True})

        # ---------------- ADMIN: NOMINEE BULK ADD ----------------
        elif path == "/api/admin/nominee/bulk-add":
            category_id = body.get("categoryId")
            names = body.get("names", [])
            
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                added = []
                current_names = {n["name"].lower() for n in cat.get("nominees", [])}
                avatars = ["cherry", "crown", "flower", "lipstick", "sunglasses", "ribbon", "wine", "mic", "rose"]
                for n_idx, raw_name in enumerate(names):
                    name = raw_name.strip().lstrip("@")
                    if name and name.lower() not in current_names:
                        av = avatars[n_idx % len(avatars)]
                        nom = {"id": f"nom_{uuid.uuid4().hex[:8]}", "name": name, "avatar": av}
                        cat.setdefault("nominees", []).append(nom)
                        current_names.add(name.lower())
                        added.append(nom)

                save_state(app_state)
                broadcast_event("NOMINEES_BULK_ADDED", {"categoryId": category_id, "nominees": added})

            return json_resp({"success": True, "addedCount": len(added), "nominees": added})

        # ---------------- ADMIN: DECLARE WINNER ----------------
        elif path == "/api/admin/category/declare-winner":
            category_id = body.get("categoryId")
            winner_id = body.get("nomineeId")

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                winner_nominee = next((n for n in cat.get("nominees", []) if n["id"] == winner_id), None)
                if not winner_nominee:
                    return json_resp({"error": "Winner nominee not found", "success": False}, 404)

                cat["winnerId"] = winner_id
                cat["isLocked"] = True

                won_count = 0
                total_payout_pool = 0
                for b in app_state["bets"]:
                    if b["categoryId"] == category_id and b.get("status") == "pending":
                        if b["nomineeId"] == winner_id:
                            b["status"] = "won"
                            payout = int(round(b["amount"] * b["oddsAtBet"]))
                            b["payoutReceived"] = payout
                            total_payout_pool += payout
                            won_count += 1
                            uid = b["userId"]
                            if uid in app_state["users"]:
                                app_state["users"][uid]["balance"] += payout
                        else:
                            b["status"] = "lost"
                            b["payoutReceived"] = 0

                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"Award decided: @{winner_nominee['name']} won '{cat['name']}' ({won_count} winning stakes settled).",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("WINNER_DECLARED", {
                    "categoryId": category_id,
                    "winnerId": winner_id,
                    "winnerName": winner_nominee["name"],
                    "categoryName": cat["name"]
                })

            return json_resp({
                "success": True,
                "winner": winner_nominee,
                "wonBetsCount": won_count,
                "totalPayout": total_payout_pool
            })

        # ---------------- ADMIN: CLEAR WINNER ----------------
        elif path == "/api/admin/category/clear-winner":
            category_id = body.get("categoryId")
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    return json_resp({"error": "Category not found", "success": False}, 404)
                
                for b in app_state["bets"]:
                    if b["categoryId"] == category_id:
                        if b.get("status") == "won":
                            payout = b.get("payoutReceived", 0)
                            uid = b["userId"]
                            if uid in app_state["users"]:
                                app_state["users"][uid]["balance"] = max(0, app_state["users"][uid]["balance"] - payout)
                        b["status"] = "pending"
                        b["payoutReceived"] = 0
                
                cat["winnerId"] = None
                cat["isLocked"] = False
                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"Winner decision for '{cat['name']}' reverted. Stakes returned to pending.",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("WINNER_CLEARED", {"categoryId": category_id})

            return json_resp({"success": True})

        # ---------------- ADMIN: RESET ----------------
        elif path == "/api/admin/reset":
            reset_type = body.get("type", "bets_only")

            with state_lock:
                if reset_type == "bets_only":
                    for b in app_state["bets"]:
                        if b.get("status") == "pending":
                            uid = b["userId"]
                            if uid in app_state["users"]:
                                app_state["users"][uid]["balance"] += b["amount"]
                    app_state["bets"] = []
                    for c in app_state["categories"]:
                        c["winnerId"] = None
                        c["isLocked"] = False
                    app_state["activity"].append({
                        "id": f"act_{uuid.uuid4().hex[:6]}",
                        "text": "All prediction pools and active stakes have been reset.",
                        "timestamp": time.time()
                    })

                elif reset_type == "defaults":
                    new_def = generate_default_state()
                    app_state["categories"] = new_def["categories"]
                    app_state["bets"] = []
                    app_state["activity"] = [{
                        "id": "act_reset",
                        "text": "Platform restored to standard 33 Lanacord Grammys categories.",
                        "timestamp": time.time()
                    }]

                save_state(app_state)
                broadcast_event("BOARD_RESET", {"type": reset_type})

            return json_resp({"success": True})

        else:
            return json_resp({"error": "Unknown API endpoint", "success": False}, 404)

    return json_resp({"error": "Method Not Allowed", "success": False}, 405)


# ==============================================================================
# STANDALONE HTTP SERVER REQUEST HANDLER
# ==============================================================================
class GrammysHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if "/api/events" not in format:
            super().log_message(format, *args)

    def do_OPTIONS(self):
        status, headers, body = handle_request("OPTIONS", self.path)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()

    def handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = queue.Queue(maxsize=100)
        with sse_lock:
            sse_subscribers.append(q)

        try:
            self.wfile.write(b"event: connected\ndata: {\"status\":\"ok\"}\n\n")
            self.wfile.flush()
        except Exception:
            with sse_lock:
                if q in sse_subscribers:
                    sse_subscribers.remove(q)
            return

        try:
            while True:
                try:
                    msg = q.get(timeout=15.0)
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with sse_lock:
                if q in sse_subscribers:
                    sse_subscribers.remove(q)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/events":
            self.handle_sse()
            return

        query = parse_qs(parsed.query)
        status, headers, body = handle_request("GET", path, query, dict(self.headers))
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = {}
        if length > 0:
            try:
                raw = self.rfile.read(length).decode("utf-8")
                body = json.loads(raw)
            except Exception:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON", "success": False}).encode("utf-8"))
                return

        query = parse_qs(parsed.query)
        status, headers, resp_body = handle_request("POST", path, query, dict(self.headers), body)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp_body)


def run_server(port=8080):
    candidates = [port] + [p for p in [8080, 8081, 8000, 3000] if p != port]
    httpd = None
    active_port = port
    for p in candidates:
        try:
            server_address = ("0.0.0.0", p)
            httpd = ThreadingHTTPServer(server_address, GrammysHTTPRequestHandler)
            active_port = p
            break
        except OSError as e:
            if e.errno == 48:
                continue
            raise

    if not httpd:
        print("Error: Could not bind to any port.")
        sys.exit(1)

    print(f"Lanacord Grammys Server running at http://localhost:{active_port}/")
    print(f"Voter Site: http://localhost:{active_port}/")
    print(f"Admin Site: http://localhost:{active_port}/admin")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
