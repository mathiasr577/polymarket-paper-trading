import requests
import json

DATA_API = "https://data-api.polymarket.com"
CLOB_HOST = "https://clob.polymarket.com"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

BET_AMOUNT = 20.0

def load_snapshot():
    try:
        with open("snapshot.json") as f:
            return json.load(f)
    except:
        return {}

def save_snapshot(snapshot):
    with open("snapshot.json", "w") as f:
        json.dump(snapshot, f)

def get_wallet_positions(address):
    try:
        r = requests.get(f"{DATA_API}/positions?user={address}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
        return []
    except:
        return []

def get_token_price(asset):
    try:
        r = requests.get(f"{CLOB_HOST}/last-trade-price?token_id={asset}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return float(r.json().get("price", 0))
        return 0
    except:
        return 0

def update_positions(state):
    snapshot = load_snapshot()
    try:
        with open("wallets.json") as f:
            wallets = json.load(f)
    except:
        return

    for wallet in wallets:
        address = wallet.get("address")
        label = wallet.get("note", address[:10])
        known_ids = snapshot.get(address, [])
        positions = get_wallet_positions(address)

        if not positions:
            continue

        current_ids = [p["conditionId"] for p in positions if float(p.get("size", 0)) > 0]

        for pos in positions:
            condition_id = pos.get("conditionId")
            asset = pos.get("asset")
            size = float(pos.get("size", 0))
            avg_price = float(pos.get("avgPrice", 0))
            title = pos.get("title", "Unknown")
            outcome = pos.get("outcome", "YES")

            existing = next((p for p in state["positions"] if p["condition_id"] == condition_id and p["wallet"] == address), None)

            if existing:
                current_price = get_token_price(asset)
                existing["current_price"] = current_price
                existing["pnl"] = (current_price - existing["entry_price"]) * existing["shares"]
                continue

            if condition_id in known_ids:
                continue

            if size > 0 and avg_price > 0:
                shares = BET_AMOUNT / avg_price
                print(f"NUEVA: {title} | {outcome} | ${BET_AMOUNT}")

                new_pos = {
                    "wallet": address,
                    "wallet_label": label,
                    "condition_id": condition_id,
                    "asset": asset,
                    "market": title,
                    "side": outcome,
                    "entry_price": avg_price,
                    "current_price": avg_price,
                    "bet_amount": BET_AMOUNT,
                    "shares": shares,
                    "pnl": 0.0,
                    "status": "open"
                }
                state["positions"].append(new_pos)
                state["total_invested"] += BET_AMOUNT

        for pos in list(state["positions"]):
            if pos["wallet"] == address and pos["condition_id"] not in current_ids and pos["status"] == "open":
                current_price = get_token_price(pos["asset"])
                pnl = (current_price - pos["entry_price"]) * pos["shares"]
                pos["pnl"] = pnl
                pos["status"] = "closed"
                pos["close_price"] = current_price
                state["total_pnl"] += pnl
                state["closed_positions"].append(pos)
                state["positions"].remove(pos)
                print(f"CERRADA: {pos['market']} | PNL: ${pnl:.2f}")

        snapshot[address] = current_ids

    save_snapshot(snapshot)