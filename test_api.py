#!/usr/bin/env python3
import urllib.request
import json
import subprocess
import time
import sys

def test_api():
    base_url = "http://127.0.0.1:8080"
    print("Testing GET /api/state...")
    req = urllib.request.Request(f"{base_url}/api/state")
    with urllib.request.urlopen(req) as resp:
        state = json.loads(resp.read().decode('utf-8'))
        cats = state.get("categories", [])
        print(f"Total categories received: {len(cats)}")
        assert len(cats) >= 33, f"Expected at least 33 categories, got {len(cats)}"
        
        # Check sections
        sections = {c["section"] for c in cats}
        print("Sections found:", sections)
        assert "Album Fan Categories" in sections
        assert "Most Likely To Categories" in sections
        assert "Best/Most/Favorite Categories" in sections

    print("Testing POST /api/user/login...")
    login_data = json.dumps({"username": "cherry_tester"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/user/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        login_res = json.loads(resp.read().decode('utf-8'))
        assert login_res["success"] is True
        user = login_res["user"]
        print(f"User logged in: {user['username']}, Balance: {user['balance']}")
        user_id = user["id"]

    # Test placing a bet
    target_cat = cats[0]
    target_nom = target_cat["nominees"][0]
    print(f"Testing POST /api/bet on {target_nom['name']} for {target_cat['name']}...")
    bet_data = json.dumps({
        "userId": user_id,
        "categoryId": target_cat["id"],
        "nomineeId": target_nom["id"],
        "amount": 100
    }).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/bet", data=bet_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        bet_res = json.loads(resp.read().decode('utf-8'))
        assert bet_res["success"] is True
        print(f"Bet placed successfully! New balance: {bet_res['newBalance']}")

    # Test adding a nominee via admin
    print("Testing POST /api/admin/nominee/add...")
    nom_data = json.dumps({
        "categoryId": target_cat["id"],
        "name": "brand_new_stan",
        "avatar": "lipstick"
    }).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/admin/nominee/add", data=nom_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        nom_res = json.loads(resp.read().decode('utf-8'))
        assert nom_res["success"] is True
        print(f"Added nominee: {nom_res['nominee']['name']}")

    # Test declaring winner
    print("Testing POST /api/admin/category/declare-winner...")
    win_data = json.dumps({
        "categoryId": target_cat["id"],
        "nomineeId": target_nom["id"]
    }).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/admin/category/declare-winner", data=win_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        win_res = json.loads(resp.read().decode('utf-8'))
        assert win_res["success"] is True
        print(f"Winner declared! Total payout: {win_res['totalPayout']}")

    # Verify user received payout
    req = urllib.request.Request(f"{base_url}/api/state?userId={user_id}")
    with urllib.request.urlopen(req) as resp:
        updated_state = json.loads(resp.read().decode('utf-8'))
        cur_user = updated_state["currentUser"]
        print(f"User updated balance after win: {cur_user['balance']} (Initial 1000 - 100 + payout {win_res['totalPayout']})")
        assert cur_user["balance"] > 900

    print("ALL TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    test_api()
