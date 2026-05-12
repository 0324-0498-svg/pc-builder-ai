import os
from flask import Flask, request, jsonify
from flask_cors import CORS

# 1. Initialize ang Flask app sa global level (Importante!)
app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return jsonify({"status": "running", "message": "AI Builder API is Live!"})

@app.route('/generate-build', methods=['POST'])
def generate_build():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        budget = float(data.get('budget', 0))
        parts = data.get('parts', [])

        categorized = {}
        for p in parts:
            cat = p['category'].upper()
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        def pick_part(category, max_price):
            options = [p for p in categorized.get(category, []) if p['price'] <= max_price]
            if not options:
                return {"name": f"No {category} found", "price": 0, "brand": "N/A"}
            return max(options, key=lambda x: x['price'])

        # Kasama na ang Motherboard sa allocation
        final_build = {
            "CPU": pick_part("CPU", budget * 0.20),
            "GPU": pick_part("GPU", budget * 0.35),
            "MOTHERBOARD": pick_part("MOTHERBOARD", budget * 0.15),
            "RAM": pick_part("RAM", budget * 0.10),
            "SSD": pick_part("SSD", budget * 0.10),
            "PSU": pick_part("PSU", budget * 0.05),
            "CASE": pick_part("CASE", budget * 0.05)
        }

        total_spent = sum(item['price'] for item in final_build.values())

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": "Optimized PC Build",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
