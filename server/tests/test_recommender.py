from pprint import pprint

try:
    from server.recommender import recommend_products
except Exception as e:
    print("Failed to import server.recommender. Make sure the recommender module exists.")
    print("Import error:", e)
    raise

def make_sample_data():
    """
    Create a target product and a list of candidate products.
    Fields used by the recommender: sku, name, category, brand, price, cf_value, web_url, image_url
    """
    target = {
        "sku": "TGT-001",
        "name": "EcoRun Lightweight Running Shoe",
        "category": "shoes_and_sneakers",
        "brand": "GreenFeet",
        "price": 79.99,
        "cf_value": 6.5,
        "web_url": "https://example.com/tgt-001",
        "image_url": None
    }

    candidates = [
        {
            "sku": "C-100",
            "name": "Budget Runner Shoe",
            "category": "shoes_and_sneakers",
            "brand": "FastFeet",
            "price": 49.99,
            "cf_value": 8.2,
            "web_url": "https://example.com/c-100",
            "image_url": None
        },
        {
            "sku": "C-101",
            "name": "GreenFeet Trail Shoe",
            "category": "shoes_and_sneakers",
            "brand": "GreenFeet",
            "price": 89.99,
            "cf_value": 5.9,
            "web_url": "https://example.com/c-101",
            "image_url": None
        },
        {
            "sku": "C-200",
            "name": "Casual Canvas Sneakers",
            "category": "tshirts",  # intentionally different category
            "brand": "CanvasCo",
            "price": 74.00,
            "cf_value": 4.0,
            "web_url": "https://example.com/c-200",
            "image_url": None
        },
        {
            "sku": "C-300",
            "name": "Premium Marathon Shoe",
            "category": "shoes_and_sneakers",
            "brand": "EliteRun",
            "price": 159.99,
            "cf_value": 3.5,
            "web_url": "https://example.com/c-300",
            "image_url": None
        },
        {
            "sku": "C-400",
            "name": "Unknown Product",
            "category": None,
            "brand": None,
            "price": None,
            "cf_value": None,
            "web_url": "https://example.com/c-400",
            "image_url": None
        },
    ]

    return target, candidates

def pretty_print_results(results):
    for i, r in enumerate(results, start=1):
        print(f"Rank {i}: sku={r.get('sku')} name={r.get('name')}")
        print(f"  score: {r.get('_rec_score'):.4f}")
        dbg = r.get('_rec_debug', {})
        print(f"  category_similarity: {dbg.get('category_similarity')}")
        print(f"  price_similarity:    {dbg.get('price_similarity')}")
        print(f"  normalized_cf:       {dbg.get('normalized_cf')}")
        print(f"  alpha/beta/gamma:    {dbg.get('alpha')}/{dbg.get('beta')}/{dbg.get('gamma')}")
        print("  product summary:", {k: r.get(k) for k in ('price','cf_value','category','brand')})
        print("-" * 60)

def main():
    target, candidates = make_sample_data()

    print("Target product:")
    pprint(target)
    print("\nCandidates:")
    pprint(candidates)
    print("\nRunning recommender (alpha=0.5, beta=0.2, gamma=1.0, top_k=5)...\n")

    results = recommend_products(
        target,
        candidates=candidates,
        top_k=5,
        alpha=0.5,
        beta=0.2,
        gamma=1.0,
        missing_cf_as_max=True,
        exclude_self=False
    )

    print("Top recommendations:")
    pretty_print_results(results)

if __name__ == "__main__":
    main()
