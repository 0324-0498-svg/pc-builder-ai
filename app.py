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

        user_budget = float(data.get('budget', 0))
        strategy = data.get('strategy', 'value')  # 'value' o 'maxout'
        parts = data.get('parts', [])

        # 1. I-grupo ang mga pyesa sa kani-kanilang kategorya
        categorized = {}
        for p in parts:
            cat_raw = p.get('category') or p.get('type') or 'UNKNOWN'
            cat = str(cat_raw).upper()
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(p)

        final_build = {}
        wallet = user_budget

        # Helper function para mag-filter ng compatibility
        def get_compatible_options(category, constraints=None):
            options = categorized.get(category.upper(), [])
            if constraints:
                for key, value in constraints.items():
                    if value:
                        options = [p for p in options if p.get(key) == value]
            return options

        # ─── STRATEGY 1: MAXIMIZE BUDGET (SAGAD PERFORMANCE) ───
        if strategy == 'maxout':
            # Dynamic Target Allocation Percentages (Gagamitin lang bilang panimulang gabay)
            # Unahin ang core foundation (CPU + GPU) para makain ang malaking budget
            
            # 1. CPU (Target: ~20% of initial wallet)
            cpu_opts = get_compatible_options("CPU")
            cpu_opts = [p for p in cpu_opts if float(p['price']) <= wallet * 0.25]
            selected_cpu = max(cpu_opts, key=lambda x: float(x['price'])) if cpu_opts else min(categorized.get("CPU", []), key=lambda x: float(x['price']), default={"price": 0, "name": "N/A"})
            final_build["CPU"] = selected_cpu
            wallet -= float(selected_cpu.get('price', 0))

            # 2. MOTHERBOARD (Dapat compatible sa CPU socket. Target: ~13% of initial wallet)
            mobo_opts = get_compatible_options("MOTHERBOARD", {"socket": selected_cpu.get("socket")})
            mobo_opts = [p for p in mobo_opts if float(p['price']) <= user_budget * 0.15]
            selected_mobo = max(mobo_opts, key=lambda x: float(x['price'])) if mobo_opts else min(get_compatible_options("MOTHERBOARD", {"socket": selected_cpu.get("socket")}), key=lambda x: float(x['price']), default={"price": 0, "name": "N/A"})
            final_build["MOTHERBOARD"] = selected_mobo
            wallet -= float(selected_mobo.get('price', 0))

            # 3. RAM (Dapat compatible sa Motherboard RAM generation)
            ram_opts = get_compatible_options("RAM", {"ram_gen": selected_mobo.get("ram_gen")})
            ram_opts = [p for p in ram_opts if float(p['price']) <= user_budget * 0.10]
            selected_ram = max(ram_opts, key=lambda x: float(x['price'])) if ram_opts else min(get_compatible_options("RAM", {"ram_gen": selected_mobo.get("ram_gen")}), key=lambda x: float(x['price']), default={"price": 0, "name": "N/A"})
            final_build["RAM"] = selected_ram
            wallet -= float(selected_ram.get('price', 0))

            # 4. GPU (Ibubuhos ang malaking bahagi ng NATITIRANG wallet!)
            gpu_opts = get_compatible_options("GPU")
            gpu_opts = [p for p in gpu_opts if float(p['price']) <= wallet - (user_budget * 0.20)] # Magtira ng konti para sa secondary parts
            if gpu_opts:
                selected_gpu = max(gpu_opts, key=lambda x: float(x['price']))
            else:
                # Fallback kung walang GPU na umubra sa target tier
                selected_gpu = min(categorized.get("GPU", []), key=lambda x: float(x['price']), default={"price": 0, "name": "N/A"})
            final_build["GPU"] = selected_gpu
            wallet -= float(selected_gpu.get('price', 0))

            # 5. ANG MGA NATITIRANG PARTS (SSD, PSU, CASE, COOLERS)
            # Hahanapin ang pinakamahal na KASYA SA NATITIRANG PERA (Wallet-aware allocation)
            other_categories = ["SSD", "PSU", "CASE", "CPU COOLER", "CASE FANS"]
            for cat in other_categories:
                # Tiyakin na may budget allowance para sa mga susunod na pyesa, hatiin natin ng patas ang tira
                safe_allocation = wallet / (len(other_categories) - other_categories.index(cat))
                cat_opts = [p for p in categorized.get(cat, []) if float(p['price']) <= wallet]
                
                if cat_opts:
                    # Kumuha ng pyesa na malapit sa safe allocation pero sagad hangga't maaari
                    target_opts = [p for p in cat_opts if float(p['price']) <= safe_allocation * 1.3]
                    if target_opts:
                        selected_part = max(target_opts, key=lambda x: float(x['price']))
                    else:
                        selected_part = min(cat_opts, key=lambda x: float(x['price']))
                else:
                    selected_part = {"name": f"No {cat} within budget", "price": 0, "brand": "N/A"}
                
                final_build[cat] = selected_part
                wallet -= float(selected_part.get('price', 0))

        # ─── STRATEGY 2: BUDGET-FRIENDLY (VALUE FOR MONEY) ───
        else:
            # Dito, kukunin natin ang pinakamurang functional options sa basic utilities 
            # para maiwan ang pondo sa solid ngunit praktikal na CPU at GPU. Target na makatipid ng 15-30% sa total budget.
            
            # 1. Mura ngunit maayos na utilities muna para makita ang pondo
            def pick_cheapest_or_mid(category, constraints=None, force_cheap=False):
                opts = get_compatible_options(category, constraints)
                if not opts:
                    return {"name": f"No {category} found", "price": 0, "brand": "N/A"}
                sorted_opts = sorted(opts, key=lambda x: float(x['price']))
                
                if force_cheap or len(sorted_opts) <= 2:
                    return sorted_opts[0] # Pinakamura
                else:
                    # Kumuha ng lower-middle class entry na subok na
                    return sorted_opts[int(len(sorted_opts) * 0.3)]

            # Utilities foundation
            final_build["CASE"] = pick_cheapest_or_mid("CASE", force_cheap=True)
            final_build["CASE FANS"] = pick_cheapest_or_mid("CASE FANS", force_cheap=True)
            final_build["CPU COOLER"] = pick_cheapest_or_mid("CPU COOLER", force_cheap=True)
            final_build["SSD"] = pick_cheapest_or_mid("SSD", force_cheap=False) # Mid-tier para tumagal
            final_build["PSU"] = pick_cheapest_or_mid("PSU", force_cheap=False) # Mid-tier para ligtas ang system
            
            current_spent = sum(float(item.get('price', 0)) for item in final_build.values())
            remaining_val_budget = (user_budget * 0.80) - current_spent # I-cap lang sa 80% ng kabuuang budget para makatipid!

            # Core Components integration batay sa natitirang "Value" Budget Pool
            cpu_opts = [p for p in categorized.get("CPU", []) if float(p['price']) <= remaining_val_budget * 0.35]
            selected_cpu = max(cpu_opts, key=lambda x: float(x['price'])) if cpu_opts else pick_cheapest_or_mid("CPU")
            final_build["CPU"] = selected_cpu

            mobo_opts = get_compatible_options("MOTHERBOARD", {"socket": selected_cpu.get("socket")})
            final_build["MOTHERBOARD"] = min(mobo_opts, key=lambda x: float(x['price'])) if mobo_opts else {"price": 0, "name": "N/A"}

            ram_opts = get_compatible_options("RAM", {"ram_gen": final_build["MOTHERBOARD"].get("ram_gen")})
            final_build["RAM"] = min(ram_opts, key=lambda x: float(x['price'])) if ram_opts else {"price": 0, "name": "N/A"}

            # Ang matitira ay para sa GPU
            already_spent = sum(float(item.get('price', 0)) for item in final_build.values())
            gpu_wallet = (user_budget * 0.85) - already_spent # Value safety margin
            gpu_opts = [p for p in categorized.get("GPU", []) if float(p['price']) <= gpu_wallet]
            final_build["GPU"] = max(gpu_opts, key=lambda x: float(x['price'])) if gpu_opts else {"name": "Integrated Graphics Solution", "price": 0, "brand": "N/A"}

        # 6. Integrated Graphics Fallback Check
        if final_build.get("GPU", {}).get("price", 0) == 0:
            cpu_name = final_build["CPU"].get("name", "").upper()
            if "G" in cpu_name or "VEGA" in cpu_name:
                final_build["GPU"] = {"name": "Integrated Radeon Graphics", "price": 0, "brand": "AMD"}
            elif "INTEL" in cpu_name and "F" not in cpu_name:
                final_build["GPU"] = {"name": "Intel UHD Graphics", "price": 0, "brand": "Intel"}

        total_spent = sum(float(item.get('price', 0)) for item in final_build.values())
        tier_suffix = "Value-Optimized Saver" if strategy == 'value' else "Max-Performance Rig"

        return jsonify({
            "status": "success",
            "total_spent": total_spent,
            "suggested_tier": f"Compatible {final_build['CPU'].get('socket', '')} ({tier_suffix})",
            "build": final_build
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
