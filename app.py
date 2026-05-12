@app.route('/generate-build', methods=['POST'])
def generate_build():
    try:
        data = request.get_json()
        budget = float(data.get('budget', 0))
        parts = data.get('parts', []) # Ito yung listahan mula sa database mo

        # 1. Hiwalayin ang parts per category
        categorized = {}
        for p in parts:
            cat = p['category']
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        # 2. Simple AI Selection Logic (Pipili ng pinakamahal na pasok sa budget)
        def pick_part(category, max_price):
            options = [p for p in categorized.get(category, []) if p['price'] <= max_price]
            if not options:
                return {"name": f"No {category} in budget", "price": 0, "brand": "N/A"}
            # Pipiliin ang pinakamahal na pasok sa budget (Best performance)
            return max(options, key=lambda x: x['price'])

        # 3. Budget Allocation (Example: 40% GPU, 20% CPU, etc.)
        final_build = {
            "GPU": pick_part("GPU", budget * 0.40),
            "CPU": pick_part("CPU", budget * 0.25),
            "RAM": pick_part("RAM", budget * 0.10),
            "SSD": pick_part("SSD", budget * 0.10),
            "PSU": pick_part("PSU", budget * 0.10),
            "CASE": pick_part("CASE", budget * 0.05)
        }

        total_spent = sum(item['price'] for item in final_build.values())

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": "Mid-Range" if budget > 40000 else "Budget",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
