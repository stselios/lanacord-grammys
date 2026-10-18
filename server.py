#!/usr/bin/env python3
"""
Lanacord Grammys - Official Gala & Fake Betting Platform Server
Zero external dependencies, powered by Python 3 standard library.
Features:
- Real-time Server-Sent Events (SSE) for instant cross-tab & cross-device updates
- Voter Betting Platform
- Admin Management & Results Control Center
- Dynamic Pari-Mutuel Odds Engine
- Persistent JSON State
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
                "text": "🥂 Welcome to the 2026 Lanacord Grammys! Place your bets on server icons.",
                "timestamp": time.time()
            }
        ],
        "meta": {
            "currencyName": "Lana Coins",
            "currencySymbol": "🍒",
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


class GrammysHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Concise logging
        if "/api/events" not in format:
            super().log_message(format, *args)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"error": message, "success": False}, status=status)

    def parse_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            return None

    def serve_file(self, file_path, content_type=None):
        if not os.path.exists(file_path):
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return
        
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_cors_headers()
        self.end_headers()

        q = queue.Queue(maxsize=100)
        with sse_lock:
            sse_subscribers.append(q)

        # Send initial connection greeting
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
                    # Heartbeat comment to keep connection alive
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
        query = parse_qs(parsed.query)

        if path == "/" or path == "/voter" or path == "/voter/":
            self.serve_file(os.path.join(STATIC_DIR, "voter.html"), "text/html; charset=utf-8")
        elif path == "/admin" or path == "/admin/":
            self.serve_file(os.path.join(STATIC_DIR, "admin.html"), "text/html; charset=utf-8")
        elif path == "/api/events":
            self.handle_sse()
        elif path == "/api/state":
            user_id = query.get("userId", [None])[0]
            data = get_public_state_data(user_id)
            self.send_json(data)
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            full_path = os.path.join(STATIC_DIR, rel_path)
            self.serve_file(full_path)
        else:
            # Try serving from static or fallback to voter.html
            candidate = os.path.join(STATIC_DIR, path.lstrip("/"))
            if os.path.exists(candidate) and os.path.isfile(candidate):
                self.serve_file(candidate)
            else:
                self.serve_file(os.path.join(STATIC_DIR, "voter.html"), "text/html; charset=utf-8")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.parse_json_body()
        if body is None:
            self.send_error_json("Invalid JSON payload", 400)
            return

        # Restrict all /api/admin/ endpoints (except /api/admin/verify) to valid admin passcode
        if path.startswith("/api/admin/") and path != "/api/admin/verify":
            admin_pwd = self.headers.get("X-Admin-Password") or (body.get("adminPassword") if isinstance(body, dict) else None)
            expected_pwd = app_state.get("meta", {}).get("adminPassword", "lanacord2026")
            if not admin_pwd or admin_pwd != expected_pwd:
                self.send_error_json("Unauthorized: Invalid Admin Passcode", 401)
                return

        # ==========================================
        # USER ENDPOINTS
        # ==========================================
        if path == "/api/user/login":
            username = body.get("username", "").strip()
            if not username:
                self.send_error_json("Username cannot be empty")
                return
            
            with state_lock:
                # Find existing user or create
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

            self.send_json({"success": True, "user": existing_user})

        elif path == "/api/user/claim":
            user_id = body.get("userId")
            with state_lock:
                if user_id not in app_state["users"]:
                    self.send_error_json("User not found", 404)
                    return
                user = app_state["users"][user_id]
                claim_amount = 250
                user["balance"] += claim_amount
                save_state(app_state)
                broadcast_event("BALANCE_UPDATED", {"userId": user_id, "newBalance": user["balance"]})

            self.send_json({"success": True, "balance": user["balance"]})

        # ==========================================
        # BETTING ENDPOINT
        # ==========================================
        elif path == "/api/bet":
            user_id = body.get("userId")
            category_id = body.get("categoryId")
            nominee_id = body.get("nomineeId")
            amount = body.get("amount")

            try:
                amount = int(amount)
            except (ValueError, TypeError):
                self.send_error_json("Invalid bet amount")
                return

            if amount <= 0:
                self.send_error_json("Bet amount must be greater than 0")
                return

            with state_lock:
                if user_id not in app_state["users"]:
                    self.send_error_json("User not found. Please log in first.")
                    return
                
                user = app_state["users"][user_id]
                if user["balance"] < amount:
                    self.send_error_json(f"Insufficient funds! You have {user['balance']} 🍒.")
                    return

                category = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not category:
                    self.send_error_json("Category not found")
                    return
                
                if category.get("isLocked") or category.get("winnerId"):
                    self.send_error_json("Betting for this category is currently locked or concluded.")
                    return

                nominee = next((n for n in category.get("nominees", []) if n["id"] == nominee_id), None)
                if not nominee:
                    self.send_error_json("Nominee not found in this category")
                    return

                # Calculate odds at time of bet
                odds_map = calculate_category_odds(category_id, app_state)
                current_odds = odds_map.get(nominee_id, {}).get("odds", 2.0)
                potential_payout = int(round(amount * current_odds))

                # Deduct balance
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

                # Add to activity feed
                activity_item = {
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"🍒 @{user['username']} placed a {amount} bet on {nominee['name']} for '{category['name']}'!",
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

            self.send_json({"success": True, "bet": new_bet, "newBalance": user["balance"]})

        # ==========================================
        # ADMIN AUTHENTICATION
        # ==========================================
        elif path == "/api/admin/verify":
            pwd = body.get("password", "")
            expected_pwd = app_state.get("meta", {}).get("adminPassword", "lanacord2026")
            if pwd == expected_pwd:
                self.send_json({"success": True})
            else:
                self.send_error_json("Invalid admin passcode", 401)
            return

        elif path == "/api/admin/change-password":
            new_pwd = body.get("newPassword", "").strip()
            if not new_pwd or len(new_pwd) < 4:
                self.send_error_json("New passcode must be at least 4 characters")
                return
            with state_lock:
                app_state["meta"]["adminPassword"] = new_pwd
                save_state(app_state)
            self.send_json({"success": True})
            return

        # ==========================================
        # ADMIN: CATEGORY MANAGEMENT
        # ==========================================
        elif path == "/api/admin/category/add":
            name = body.get("name", "").strip()
            section = body.get("section", "Album Fan Categories").strip()
            description = body.get("description", "").strip()

            if not name:
                self.send_error_json("Category name is required")
                return

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
                    "text": f"✨ New Grammys Category added: '{name}' in {section}!",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("CATEGORY_ADDED", {"category": new_cat})

            self.send_json({"success": True, "category": new_cat})

        elif path == "/api/admin/category/delete":
            category_id = body.get("categoryId")
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                app_state["categories"] = [c for c in app_state["categories"] if c["id"] != category_id]
                # Refund any pending bets for this category
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
                    "text": f"🗑️ Category '{cat['name']}' was removed by an Admin ({refunded_count} bets refunded).",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("CATEGORY_DELETED", {"categoryId": category_id})

            self.send_json({"success": True})

        elif path == "/api/admin/category/edit":
            category_id = body.get("categoryId")
            name = body.get("name", "").strip()
            section = body.get("section", "").strip()
            description = body.get("description", "").strip()

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                if name:
                    cat["name"] = name
                if section:
                    cat["section"] = section
                if description:
                    cat["description"] = description

                save_state(app_state)
                broadcast_event("CATEGORY_EDITED", {"category": cat})

            self.send_json({"success": True, "category": cat})

        elif path == "/api/admin/category/lock":
            category_id = body.get("categoryId")
            locked = bool(body.get("isLocked", True))

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                cat["isLocked"] = locked
                save_state(app_state)
                broadcast_event("CATEGORY_LOCKED", {"categoryId": category_id, "isLocked": locked})

            self.send_json({"success": True, "isLocked": locked})

        # ==========================================
        # ADMIN: NOMINEE / MEMBER MANAGEMENT
        # ==========================================
        elif path == "/api/admin/nominee/add":
            category_id = body.get("categoryId")
            name = body.get("name", "").strip()
            avatar = body.get("avatar", "cherry").strip()

            if not name:
                self.send_error_json("Nominee member name is required")
                return

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                # Check duplicate
                if any(n["name"].lower() == name.lower() for n in cat.get("nominees", [])):
                    self.send_error_json(f"Nominee '{name}' is already in this category.")
                    return

                new_nominee = {
                    "id": f"nom_{uuid.uuid4().hex[:8]}",
                    "name": name,
                    "avatar": avatar
                }
                if "nominees" not in cat:
                    cat["nominees"] = []
                cat["nominees"].append(new_nominee)

                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"🌟 Nominee added: @{name} in '{cat['name']}'!",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("NOMINEE_ADDED", {"categoryId": category_id, "nominee": new_nominee})

            self.send_json({"success": True, "nominee": new_nominee})

        elif path == "/api/admin/nominee/delete":
            category_id = body.get("categoryId")
            nominee_id = body.get("nomineeId")

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                nominee = next((n for n in cat.get("nominees", []) if n["id"] == nominee_id), None)
                cat["nominees"] = [n for n in cat.get("nominees", []) if n["id"] != nominee_id]

                # Refund bets placed specifically on this nominee
                refunded_count = 0
                for b in app_state["bets"]:
                    if b["categoryId"] == category_id and b["nomineeId"] == nominee_id and b.get("status") == "pending":
                        uid = b["userId"]
                        if uid in app_state["users"]:
                            app_state["users"][uid]["balance"] += b["amount"]
                            refunded_count += 1
                        b["status"] = "refunded"

                if nominee:
                    app_state["activity"].append({
                        "id": f"act_{uuid.uuid4().hex[:6]}",
                        "text": f"❌ @{nominee['name']} was removed from '{cat['name']}' ({refunded_count} bets refunded).",
                        "timestamp": time.time()
                    })

                save_state(app_state)
                broadcast_event("NOMINEE_DELETED", {"categoryId": category_id, "nomineeId": nominee_id})

            self.send_json({"success": True})

        elif path == "/api/admin/nominee/bulk-add":
            category_id = body.get("categoryId")
            names = body.get("names", []) # array of strings
            
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                added = []
                current_names = {n["name"].lower() for n in cat.get("nominees", [])}
                avatars = ["cherry", "crown", "flower", "lipstick", "sunglasses", "ribbon", "wine", "mic", "rose"]
                for n_idx, raw_name in enumerate(names):
                    name = raw_name.strip().lstrip("@")
                    if name and name.lower() not in current_names:
                        av = avatars[n_idx % len(avatars)]
                        nom = {
                            "id": f"nom_{uuid.uuid4().hex[:8]}",
                            "name": name,
                            "avatar": av
                        }
                        cat.setdefault("nominees", []).append(nom)
                        current_names.add(name.lower())
                        added.append(nom)

                save_state(app_state)
                broadcast_event("NOMINEES_BULK_ADDED", {"categoryId": category_id, "nominees": added})

            self.send_json({"success": True, "addedCount": len(added), "nominees": added})

        # ==========================================
        # ADMIN: DECLARE WINNER & SETTLE BETS
        # ==========================================
        elif path == "/api/admin/category/declare-winner":
            category_id = body.get("categoryId")
            winner_id = body.get("nomineeId")

            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                winner_nominee = next((n for n in cat.get("nominees", []) if n["id"] == winner_id), None)
                if not winner_nominee:
                    self.send_error_json("Winner nominee not found")
                    return

                cat["winnerId"] = winner_id
                cat["isLocked"] = True

                # Settle all bets for this category
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
                            # Credit user
                            uid = b["userId"]
                            if uid in app_state["users"]:
                                app_state["users"][uid]["balance"] += payout
                        else:
                            b["status"] = "lost"
                            b["payoutReceived"] = 0

                app_state["activity"].append({
                    "id": f"act_{uuid.uuid4().hex[:6]}",
                    "text": f"🏆 GRAMMY WINNER! @{winner_nominee['name']} wins '{cat['name']}'! {won_count} winning bets paid out ({total_payout_pool} 🍒 total)!",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("WINNER_DECLARED", {
                    "categoryId": category_id,
                    "winnerId": winner_id,
                    "winnerName": winner_nominee["name"],
                    "categoryName": cat["name"]
                })

            self.send_json({
                "success": True,
                "winner": winner_nominee,
                "wonBetsCount": won_count,
                "totalPayout": total_payout_pool
            })

        elif path == "/api/admin/category/clear-winner":
            category_id = body.get("categoryId")
            with state_lock:
                cat = next((c for c in app_state["categories"] if c["id"] == category_id), None)
                if not cat:
                    self.send_error_json("Category not found")
                    return
                
                # Revert bets for this category: deduct payouts if won, set to pending
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
                    "text": f"🔄 Winner for '{cat['name']}' was reset. Bets returned to pending.",
                    "timestamp": time.time()
                })
                save_state(app_state)
                broadcast_event("WINNER_CLEARED", {"categoryId": category_id})

            self.send_json({"success": True})

        # ==========================================
        # ADMIN: RESET ACTIONS
        # ==========================================
        elif path == "/api/admin/reset":
            reset_type = body.get("type", "bets_only")

            with state_lock:
                if reset_type == "bets_only":
                    # Refund all pending bets and clear all bets
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
                        "text": "🧹 Admin reset all betting pools and bets. Ready for a fresh round!",
                        "timestamp": time.time()
                    })

                elif reset_type == "defaults":
                    new_def = generate_default_state()
                    app_state["categories"] = new_def["categories"]
                    app_state["bets"] = []
                    app_state["activity"] = [{
                        "id": "act_reset",
                        "text": "✨ Board restored to default Lanacord Grammys categories and nominees!",
                        "timestamp": time.time()
                    }]

                save_state(app_state)
                broadcast_event("BOARD_RESET", {"type": reset_type})

            self.send_json({"success": True})

        else:
            self.send_error_json("Unknown API endpoint", 404)


def run_server(port=8080):
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, GrammysHTTPRequestHandler)
    print(f"🎵 Lanacord Grammys Server running at http://localhost:{port}/")
    print(f"👑 Voter Site: http://localhost:{port}/")
    print(f"🛡️  Admin Site: http://localhost:{port}/admin")
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
