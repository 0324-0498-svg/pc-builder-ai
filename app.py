@app.route('/generate-build', methods=['POST'])
def generate_build():
    try:
        data = request.get_json()
        budget = float(data.get('budget', 0))
        parts = data.get('parts', [])

        categorized = {}
        for p in parts:
            cat = p['category'].upper() # Siguraduhing uppercase para iwas error
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        def pick_part(category, max_price):
            options = [p for p in categorized.get(category, []) if p['price'] <= max_price]
            if not options:
                return {"name": f"No {category} found", "price": 0, "brand": "N/A"}
            return max(options, key=lambda x: x['price'])

        # IN-UPDATE NA ALLOCATION: Isinama ang Motherboard (MB)
        # Binawasan natin nang konti ang GPU at CPU para magkasya ang MB
        final_build = {
            "CPU": pick_part("CPU", budget * 0.20),
            "GPU": pick_part("GPU", budget * 0.35),
            "MOTHERBOARD": pick_part("MOTHERBOARD", budget * 0.15), # <--- Eto na siya!
            "RAM": pick_part("RAM", budget * 0.10),
            "SSD": pick_part("SSD", budget * 0.10),
            "PSU": pick_part("PSU", budget * 0.05),
            "CASE": pick_part("CASE", budget * 0.05)
        }

        total_spent = sum(item['price'] for item in final_build.values())

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": "Complete System Build",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
