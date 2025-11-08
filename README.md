## Carbon0
By Chris Wu, Safa Obuz, Ariji Chakma, Kaijie Lai

### Project Explanation
Carbon0 is a browser extension that analyzes product carbon footprints and finds eco-friendly alternatives. The extension extracts product information from major e-commerce platforms and sends it to a Flask backend for carbon footprint analysis.

### Tech Stack
- **Frontend**: Chrome Extension (Manifest V3)
- **Backend**: Flask (Python)
- **Supported Platforms**: Amazon, Walmart, Etsy, Best Buy, Target, eBay

### Features
- Multi-platform product information extraction
- Automatic carbon footprint analysis
- Eco-friendly alternative suggestions
- Review extraction (up to 3 examples)
- Shipping and seller information tracking

### To Run:

#### Backend Setup:
```bash
cd server
pip install -r requirements.txt
python app.py
```

The backend will run on `http://localhost:5000`

#### Extension Setup:
1. Open Chrome/Edge and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked" and select the extension folder
4. Navigate to any supported product page:
   - Amazon: `https://www.amazon.com/...`
   - Walmart: `https://www.walmart.com/...`
   - Etsy: `https://www.etsy.com/...`
   - Best Buy: `https://www.bestbuy.com/...`
   - Target: `https://www.target.com/...`
   - eBay: `https://www.ebay.com/...`
5. Click the Carbon0 extension icon in the toolbar
6. Click "Analyze Product" to extract and send product data

### API Endpoint

**POST** `/api/product`

Receives product data in JSON format:
```json
{
  "platform": "Amazon",
  "url": "https://www.amazon.com/...",
  "image": "https://...",
  "name": "Product Name",
  "price": "$29.99",
  "rating": "4.5 out of 5 stars",
  "shipper": null,
  "seller": "Amazon.com",
  "reviews": ["Review 1", "Review 2", "Review 3"],
  "shippingFrom": "United States",
  "fulfilledBy": null,
  "availability": "In Stock",
  "brand": "Brand Name"
}
```

### Video Demonstration
N/A yet
