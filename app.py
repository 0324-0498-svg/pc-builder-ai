import os
from flask import Flask, request, jsonify
from flask_cors import CORS

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

        # 1. Categorize parts
        categorized = {}
        for p in parts:
            cat_raw = p.get('category') or p.get('type') or 'UNKNOWN'
            cat = str(cat_raw).upper()
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        def pick_part(category, max_price):
            options = [p for p in categorized.get(category.upper(), []) if float(p['price']) <= max_price]
            if not options:
                return {"name": f"No {category} found", "price": 0, "brand": "N/A", "type": category}
            return max(options, key=lambda x: float(x['price']))

        # 2. Updated Budget Allocation (Adjusted percentages to include new parts)
        # Binawasan natin ng konti ang CPU/GPU para magka-budget sa Cooler at Fans
        final_build = {
            "CPU": pick_part("CPU", budget * 0.18),
            "GPU": pick_part("GPU", budget * 0.30),
            "MOTHERBOARD": pick_part("MOTHERBOARD", budget * 0.12),
            "RAM": pick_part("RAM", budget * 0.08),
            "SSD": pick_part("SSD", budget * 0.08),
            "PSU": pick_part("PSU", budget * 0.07),
            "CASE": pick_part("CASE", budget * 0.07),
            "CPU COOLER": pick_part("CPU COOLER", budget * 0.05),
            "CASE FANS": pick_part("CASE FANS", budget * 0.05)
        }

        # 3. Smart Logic: Integrated Graphics Check
        # Kung walang nahanap na GPU sa budget, i-check kung ang CPU ay may Integrated Graphics (G series)
        if final_build["GPU"]["price"] == 0:
            cpu_name = final_build["CPU"].get("name", "").upper()
            if "G" in cpu_name or "VEGA" in cpu_name:
                 final_build["GPU"] = {"name": "Integrated Radeon Graphics", "price": 0, "brand": "AMD", "type": "GPU"}
            elif "INTEL" in cpu_name and "F" not in cpu_name:
                 final_build["GPU"] = {"name": "Intel UHD Graphics", "price": 0, "brand": "Intel", "type": "GPU"}

        total_spent = sum(float(item['price']) for item in final_build.values())

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": "Optimized PC Build with Cooling",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
