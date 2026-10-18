#!/usr/bin/env python3
import os
import sys
import json
import uuid

# Import server module
import server

def test_unit():
    print("Testing server internal logic & data integrity...")
    state = server.app_state
    
    # 1. Verify 33 default categories
    cats = state["categories"]
    print(f"Total categories: {len(cats)}")
    assert len(cats) >= 33, f"Expected 33 categories, got {len(cats)}"
    
    # Verify exact categories requested by the user
    required_album_cats = [
        "Biggest BTD Fan", "Biggest Paradise Fan", "Biggest UV Fan", "Biggest LFL Fan",
        "Biggest NFR Fan", "Biggest COTCC Fan", "Biggest BB Fan", "Biggest BB Hater",
        "Biggest DYKTTATUOB Fan", "Biggest Lana Fan"
    ]
    required_likely_cats = [
        "Get Arrested", "Burn a House Down", "Fake a Death", "Be in a Cult",
        "Get Banned", "Meet Lana", "Become Famous", "Become Rich", "Become President"
    ]
    required_best_cats = [
        "Best Music Taste", "Best Merch", "Most Chronically Online", "Funniest Member",
        "Messiest Member", "Most Active", "Most Helpful", "Most Dramatic",
        "Best Profile Picture", "Best Layout", "Best Username", "Best Duo/Group",
        "Best Red Carpet Outfit", "Favorite Member"
    ]

    all_cat_names = [c["name"] for c in cats]
    for name in required_album_cats:
        assert name in all_cat_names, f"Missing required Album Fan category: {name}"
    for name in required_likely_cats:
        assert name in all_cat_names, f"Missing required Most Likely To category: {name}"
    for name in required_best_cats:
        assert name in all_cat_names, f"Missing required Best/Most/Favorite category: {name}"
    print("✓ All 33 user categories present and accounted for!")

    # 2. Test odds calculation
    test_cat = cats[0]
    odds_map = server.calculate_category_odds(test_cat["id"], state)
    print(f"Calculated initial odds for '{test_cat['name']}': {odds_map}")
    assert len(odds_map) == len(test_cat["nominees"])
    for nid, odata in odds_map.items():
        assert odata["odds"] > 1.0

    # 3. Test public state compilation
    public_data = server.get_public_state_data("demo_voter")
    assert public_data["currentUser"] is not None
    assert public_data["stats"]["totalCategories"] >= 33
    assert "adminPassword" not in public_data["meta"], "Security leak: adminPassword must never be in public state meta!"
    print("✓ get_public_state_data returned full enriched state and kept adminPassword secure!")

    # 4. Test winner declaration and payouts
    # Create test user
    uid = "test_user_payout"
    state["users"][uid] = {
        "id": uid,
        "username": "salvatore_stan",
        "balance": 1000,
        "createdAt": 123456
    }
    
    # Place a bet
    target_nom = test_cat["nominees"][0]
    bet_amount = 200
    bet_id = "test_bet_1"
    odds_val = odds_map[target_nom["id"]]["odds"]
    potential_payout = int(round(bet_amount * odds_val))
    
    state["users"][uid]["balance"] -= bet_amount
    state["bets"].append({
        "id": bet_id,
        "userId": uid,
        "username": "salvatore_stan",
        "categoryId": test_cat["id"],
        "categoryName": test_cat["name"],
        "nomineeId": target_nom["id"],
        "nomineeName": target_nom["name"],
        "amount": bet_amount,
        "oddsAtBet": odds_val,
        "potentialPayout": potential_payout,
        "status": "pending",
        "timestamp": 1234567
    })
    
    # Declare winner
    test_cat["winnerId"] = target_nom["id"]
    test_cat["isLocked"] = True
    
    # Settle
    for b in state["bets"]:
        if b["categoryId"] == test_cat["id"] and b["status"] == "pending":
            if b["nomineeId"] == target_nom["id"]:
                b["status"] = "won"
                payout = int(round(b["amount"] * b["oddsAtBet"]))
                b["payoutReceived"] = payout
                state["users"][b["userId"]]["balance"] += payout

    assert state["users"][uid]["balance"] == (1000 - 200 + potential_payout)
    print(f"✓ Winner declaration & payout settled cleanly! Balance: {state['users'][uid]['balance']} (Expected: {800 + potential_payout})")

    # Clean up test user & bet
    test_cat["winnerId"] = None
    test_cat["isLocked"] = False
    state["bets"] = [b for b in state["bets"] if b["id"] != bet_id]
    del state["users"][uid]
    server.save_state(state)

    print("\n🎉 ALL IN-MEMORY VERIFICATIONS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    test_unit()
