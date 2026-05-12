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

        # 1. Categorize parts and store compatibility info
        categorized = {}
        for p in parts:
            # Kinukuha na natin pati 'socket' at 'ram_gen' mula sa input
            cat_raw = p.get('category') or p.get('type') or 'UNKNOWN'
            cat = str(cat_raw).upper()
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        def pick_part(category, max_price, constraints=None):
            options = categorized.get(category.upper(), [])
            
            # Apply Compatibility Constraints
            if constraints:
                for key, value in constraints.items():
                    if value: # Siguraduhin na may value ang constraint
                        options = [p for p in options if p.get(key) == value]

            # Final filter by budget
            options = [p for p in options if float(p['price']) <= max_price]

            if not options:
                return {"name": f"No compatible {category} found", "price": 0, "brand": "N/A"}
            
            # Pipiliin ang pinakamahal na pasok sa budget para sa best performance
            return max(options, key=lambda x: float(x['price']))

        # --- AI SELECTION ORDER (Critical for Compatibility) ---

        # 1. Pick CPU First
        selected_cpu = pick_part("CPU", budget * 0.18)
        
        # 2. Match Motherboard to CPU Socket
        selected_mobo = pick_part("MOTHERBOARD", budget * 0.12, 
                                  constraints={"socket": selected_cpu.get("socket")})
        
        # 3. Match RAM to Motherboard Generation (DDR4/DDR5)
        selected_ram = pick_part("RAM", budget * 0.08, 
                                 constraints={"ram_gen": selected_mobo.get("ram_gen")})

        # 4. Fill in the rest (General parts)
        final_build = {
            "CPU": selected_cpu,
            "MOTHERBOARD": selected_mobo,
            "RAM": selected_ram,
            "GPU": pick_part("GPU", budget * 0.30),
            "SSD": pick_part("SSD", budget * 0.08),
            "PSU": pick_part("PSU", budget * 0.07),
            "CASE": pick_part("CASE", budget * 0.07),
            "CPU COOLER": pick_part("CPU COOLER", budget * 0.05),
            "CASE FANS": pick_part("CASE FANS", budget * 0.05)
        }

        # 5. Integrated Graphics Check (Same as before)
        if final_build["GPU"]["price"] == 0:
            cpu_name = final_build["CPU"].get("name", "").upper()
            if "G" in cpu_name or "VEGA" in cpu_name:
                final_build["GPU"] = {"name": "Integrated Radeon Graphics", "price": 0, "brand": "AMD"}
            elif "INTEL" in cpu_name and "F" not in cpu_name:
                final_build["GPU"] = {"name": "Intel UHD Graphics", "price": 0, "brand": "Intel"}

        total_spent = sum(float(item['price']) for item in final_build.values())

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": f"Compatible {selected_cpu.get('socket', '')} Build",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
