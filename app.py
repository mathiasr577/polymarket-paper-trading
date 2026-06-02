from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import json
from tracker import update_positions

app = Flask(__name__)

state = {
    "balance": 150.0,
    "total_invested": 0.0,
    "total_pnl": 0.0,
    "positions": [],
    "closed_positions": []
}

def job():
    update_positions(state)

scheduler = BackgroundScheduler()
scheduler.add_job(job, 'interval', seconds=30)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    open_pnl = sum(p["pnl"] for p in state["positions"])
    return jsonify({
        "balance": round(state["balance"], 2),
        "total_invested": round(state["total_invested"], 2),
        "total_pnl": round(state["total_pnl"] + open_pnl, 2),
        "open_positions": len(state["positions"]),
        "closed_positions": len(state["closed_positions"]),
        "positions": state["positions"],
        "closed_positions_list": state["closed_positions"]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5002)
