def calculate_carbon_footprint(data):
    # 1. Material
    cf_material = sum(m["weight"] * m["emission_factor"] for m in data["materials"])

    # 2. Manufacturing
    cf_manufacturing = cf_material * data["manufacturing_factor"]["value"]

    # 3. Tranportation
    cf_transport = (
        data["product_weight"]["value"]
        * data["transport"]["distance_km"]
        * data["transport"]["emission_factor_ton_km"]
        / 1000
    )  # Transfer kg CO₂e

    # 4. Packaging
    cf_packaging = (
        data["packaging"]["weight"] * data["packaging"]["emission_factor"]
    )

    cf_total = cf_material + cf_manufacturing + cf_transport + cf_packaging

    return {
        "cf_total": cf_total,
        "breakdown": {
            "material": cf_material,
            "manufacturing": cf_manufacturing,
            "transport": cf_transport,
            "packaging": cf_packaging,
        }
    }
