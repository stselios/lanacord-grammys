# 🏆 Lanacord Grammys 2026 — Fake Betting Gala

A custom-built, luxury fake betting and ceremony director platform for the Lanacord Grammys. Complete with real-time bidirectional synchronization, dynamic odds, luxury Lana Del Rey aesthetics, interactive betslips, and an executive admin suite.

---

## 🚀 Quick Start

The server has zero external dependencies (powered entirely by Python 3 standard library):

```bash
cd /Users/sakistselios/Downloads/lanacord-grammys
./start.sh 8080
```

Once running:
- **👑 Voter Betting Site**: [http://localhost:8080/](http://localhost:8080/)
- **🛡️ Admin Suite**: [http://localhost:8080/admin](http://localhost:8080/admin)

*(Both sites can be opened in side-by-side tabs or separate windows to watch real-time updates happen live!)*

---

## ✨ Features

### 1. 👑 Voter Platform (`/`)
- **Luxury Aesthetic**: Vintage Hollywood noir, velvet burgundy, champagne gold shimmer, and custom Lana Del Rey iconography (cherries 🍒, ribbons, cigarettes, sunglasses).
- **Voter Profiles & Wallet**:
  - Voters sign in with their Discord username (`@username`).
  - Starts with **1,000 🍒 Lana Coins**.
  - Emergency Daily Claim button (+250 🍒) if balance runs low.
- **Dynamic Pari-Mutuel Odds Engine**:
  - Odds react dynamically as the community places bets on nominees.
  - Potential payout calculator with custom presets (`25`, `50`, `100`, `250`, `500`, `ALL IN!`).
- **Interactive Confetti & Audio**:
  - Zero-asset Web Audio API chimes for placing bets, winning, and clicking.
  - Realistic multi-color canvas confetti on bet placement and ceremony victories.
- **My Betslip**:
  - Live tracking of all pending, won, lost, and refunded bets with exact payouts.
- **Live Leaderboard**:
  - Real-time ranking of high rollers and biggest winners across the server.
- **Gala Wire Marquee**:
  - Horizontal live ticker displaying server-wide betting activity in real time.

---

### 2. 🛡️ Executive Admin Suite (`/admin`)
- **🔒 Passcode-Protected Gate**:
  - The admin suite and all admin APIs are locked behind a secure passcode (Default: `lanacord2026`).
  - Unauthorized visitors cannot access admin controls, add/remove members, or declare winners.
  - Hosts can change the passcode anytime directly in the dashboard via the **🔑 Change Passcode** button!
- **Instant Cross-Site Sync (Server-Sent Events)**:
  - Any category created or deleted, nominee added or removed, or winner declared immediately updates **all open voter screens** without refreshing!
- **Category Management**:
  - Add new categories with custom sections, names, and descriptions.
  - Lock/unlock betting pools at any time before ceremony announcements.
  - Delete categories (automatically refunds pending bets back to users).
- **Member / Nominee Management**:
  - Add individual nominees with customizable avatar icons.
  - **⚡ Bulk Add Members**: Paste lists of Discord usernames (e.g. `@alice, @bob, @charlie` or separated by newlines) to populate categories in seconds!
  - Remove nominees (automatically refunds bets placed on them).
- **Declare Winners & Settle Bets**:
  - With one click, declare a nominee as the category winner.
  - Automatically calculates and credits payouts to all victorious bettors!
  - Triggers server-wide victory celebration, brass fanfare, and confetti.
  - Ability to undo / clear winner if a mistake was made.
- **Ceremony Presets & Reset**:
  - Clear all bets for a fresh round.
  - Restore the official 33 default categories anytime.

---

## 📋 Included Grammys Categories (33 Total)

### 💿 Album Fan Categories (10)
1. **Biggest BTD Fan**
2. **Biggest Paradise Fan**
3. **Biggest UV Fan**
4. **Biggest LFL Fan**
5. **Biggest NFR Fan**
6. **Biggest COTCC Fan**
7. **Biggest BB Fan**
8. **Biggest BB Hater**
9. **Biggest DYKTTATUOB Fan**
10. **Biggest Lana Fan**

### 🚨 Most Likely To Categories (9)
1. **Get Arrested**
2. **Burn a House Down**
3. **Fake a Death**
4. **Be in a Cult**
5. **Get Banned**
6. **Meet Lana**
7. **Become Famous**
8. **Become Rich**
9. **Become President**

### 👑 Best / Most / Favorite Categories (14)
1. **Best Music Taste**
2. **Best Merch**
3. **Most Chronically Online**
4. **Funniest Member**
5. **Messiest Member**
6. **Most Active**
7. **Most Helpful**
8. **Most Dramatic**
9. **Best Profile Picture**
10. **Best Layout**
11. **Best Username**
12. **Best Duo/Group**
13. **Best Red Carpet Outfit**
14. **Favorite Member**

---

## 🌐 Sharing with Your Discord Server

To let server members on your local Wi-Fi or across the internet participate:
1. **Local Network**: Share `http://<your-mac-local-ip>:8080/`
2. **Online via Cloudflare Tunnel (Free)**:
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```
3. **Online via ngrok (Free)**:
   ```bash
   ngrok http 8080
   ```
