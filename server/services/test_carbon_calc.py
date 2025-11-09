import math
from server.services.carbon_calc import calculate_carbon_footprint

carbon_input = {
    "materials": [
        {
            "name": "Polyester",
            "weight": 0.35,
            "weight_source": "exact from page",
            "emission_factor": 5.5,
            "emission_factor_source": "DEFRA 2023 database"
        },
        {
            "name": "Rubber",
            "weight": 0.25,
            "weight_source": "retrieved from web",
            "emission_factor": 3.2,
            "emission_factor_source": "Ecoinvent v3.9"
        }
    ],
    "manufacturing_factor": {
        "value": 0.12,
        "source": "Default for footwear category (CarbonCalc.py constant table)"
    },
    "transport": {
        "origin": "Vietnam",
        "distance_km": 9800,
        "mode": "sea",
        "emission_factor_ton_km": 0.01,
        "source": "retrieved from web (World Bank database)"
    },
    "packaging": {
        "weight": 0.08,
        "emission_factor": 1.2,
        "source": "DEFRA 2023 packaging factors"
    },
    "product_weight": {
        "value": 0.6,
        "source": "retrieved from web"
    }
}

def main():
    result = calculate_carbon_footprint(carbon_input)
    print("Carbon footprint result:")
    print(result)

    # Expected values (calculated from the same formula used in carbon_calc.py)
    expected_material = 0.35 * 5.5 + 0.25 * 3.2  # = 2.725
    expected_manufacturing = expected_material * 0.12  # = 0.327
    expected_transport = 0.6 * 9800 * 0.01 / 1000  # = 0.0588
    expected_packaging = 0.08 * 1.2  # = 0.096
    expected_total = expected_material + expected_manufacturing + expected_transport + expected_packaging  # = 3.2068

    # Tolerance for float comparisons
    tol = 1e-8

    assert math.isclose(result["breakdown"]["material"], expected_material, rel_tol=0, abs_tol=tol), \
        f"material mismatch: {result['breakdown']['material']} != {expected_material}"
    assert math.isclose(result["breakdown"]["manufacturing"], expected_manufacturing, rel_tol=0, abs_tol=tol), \
        f"manufacturing mismatch: {result['breakdown']['manufacturing']} != {expected_manufacturing}"
    assert math.isclose(result["breakdown"]["transport"], expected_transport, rel_tol=0, abs_tol=tol), \
        f"transport mismatch: {result['breakdown']['transport']} != {expected_transport}"
    assert math.isclose(result["breakdown"]["packaging"], expected_packaging, rel_tol=0, abs_tol=tol), \
        f"packaging mismatch: {result['breakdown']['packaging']} != {expected_packaging}"
    assert math.isclose(result["cf_total"], expected_total, rel_tol=0, abs_tol=tol), \
        f"total mismatch: {result['cf_total']} != {expected_total}"

    print("All checks passed. Computed total:", result["cf_total"])

if __name__ == "__main__":
    main()
