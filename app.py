from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # This allows your InfinityFree PHP site to access this API

@app.route('/generate-build', methods=['POST', 'GET'])
def generate_build():
    # Get budget from the request (default to 0 if not provided)
    data = request.get_json() if request.is_json else request.args
    budget = float(data.get('budget', 0))

    if budget < 8000 or budget > 100000:
        return jsonify({"error": "Budget must be between ₱8,000 and ₱100,000"}), 400

    # Your defined AI Logic: Budget Allocation
    allocation = {
        "gpu": budget * 0.40,
        "cpu": budget * 0.25,
        "motherboard": budget * 0.10,
        "ram": budget * 0.10,
        "storage": budget * 0.10,
        "psu_case": budget * 0.05
    }

    # In a full system, you would query your DB here. 
    # For now, we return the "Target Prices" for each category.
    response = {
        "status": "success",
        "total_budget": budget,
        "target_allocation": allocation,
        "suggested_tier": "Entry" if budget < 30000 else "Mid-Range" if budget < 70000 else "High-End"
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
