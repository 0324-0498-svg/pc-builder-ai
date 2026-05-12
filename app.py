from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

@app.route('/generate-build', methods=['POST']) # Ibalik sa POST
def generate_build():
    try:
        # Kunin ang data mula sa JSON body
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        budget = float(data.get('budget', 0))
        purpose = data.get('purpose', 'gaming')
        era = data.get('era', 'all')
        parts = data.get('parts', []) # Ito yung listahan mula sa DB mo

        if budget < 8000:
            return jsonify({"status": "error", "message": "Budget is too low"}), 400

        # Simple Logic para sa response (dahil kailangan ng frontend mo ang 'build' object)
        # Sa ngayon, ibabalik muna natin ang allocation para hindi mag-error ang JS
        response = {
            "status": "success",
            "total_spent": budget,
            "suggested_tier": "Entry" if budget < 30000 else "Mid-Range" if budget < 70000 else "High-End",
            "build": {
                "CPU": {"name": "Calculating...", "price": budget * 0.25, "brand": "AI Processing"},
                "GPU": {"name": "Calculating...", "price": budget * 0.40, "brand": "AI Processing"},
                "RAM": {"name": "Calculating...", "price": budget * 0.10, "brand": "AI Processing"},
                "SSD": {"name": "Calculating...", "price": budget * 0.10, "brand": "AI Processing"},
                "PSU": {"name": "Calculating...", "price": budget * 0.10, "brand": "AI Processing"},
                "CASE": {"name": "Calculating...", "price": budget * 0.05, "brand": "AI Processing"}
            }
        }
        return jsonify(response)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
