const API_URL = 'http://localhost:5000/api/product';

document.getElementById('readBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  const supportedPlatforms = ['amazon.com', 'walmart.com', 'etsy.com', 'bestbuy.com', 'target.com', 'ebay.com'];
  const isSupported = supportedPlatforms.some(platform => tab.url.includes(platform));
  
  if (!isSupported) {
    document.getElementById('productInfo').innerHTML = 
      '<div class="error">Please navigate to a supported product page (Amazon, Walmart, Etsy, Best Buy, Target, or eBay)</div>';
    return;
  }

  document.getElementById('readBtn').disabled = true;
  document.getElementById('readBtn').textContent = 'Extracting...';
  document.getElementById('productInfo').innerHTML = '<div class="loading">Extracting product information...</div>';

  chrome.tabs.sendMessage(tab.id, { action: 'getProductInfo' }, async (response) => {
    const infoDiv = document.getElementById('productInfo');
    
    if (!response) {
      infoDiv.innerHTML = '<div class="error">Could not extract product information. Make sure you are on a product page.</div>';
      document.getElementById('readBtn').disabled = false;
      document.getElementById('readBtn').textContent = 'Analyze Product';
      return;
    }

    const hasAnyData = response.title || response.price || response.rating || response.image;
    if (!hasAnyData) {
      infoDiv.innerHTML = '<div class="error">Could not extract product information. The page structure may have changed.</div>';
      document.getElementById('readBtn').disabled = false;
      document.getElementById('readBtn').textContent = 'Analyze Product';
      return;
    }

    let html = '';
    html += `<div class="product-title">${response.title || 'Unknown Product'}</div>`;
    html += `<div class="product-detail"><strong>Platform:</strong> ${response.platform || 'Unknown'}</div>`;
    
    if (response.price) {
      html += `<div class="product-detail"><strong>Price:</strong> ${response.price}</div>`;
    }
    if (response.rating) {
      html += `<div class="product-detail"><strong>Rating:</strong> ${response.rating}</div>`;
    }
    if (response.soldBy) {
      html += `<div class="product-detail"><strong>Sold By:</strong> ${response.soldBy}</div>`;
    }
    if (response.shipsFrom) {
      html += `<div class="product-detail"><strong>Ships From:</strong> ${response.shipsFrom}</div>`;
    }
    if (response.image) {
      html += `<div class="product-detail"><img src="${response.image}" style="max-width: 100%; height: auto; margin-top: 10px; border-radius: 5px;" /></div>`;
    }

    infoDiv.innerHTML = html;

    const productData = {
      platform: response.platform || null,
      url: response.url || tab.url,
      image: response.image || null,
      name: response.title || null,
      price: response.price || null,
      rating: response.rating || null,
      shipper: response.shipsFrom || null,
      seller: response.soldBy || response.seller || null,
      reviews: response.reviews || [],
      shippingFrom: response.shipsFrom || null,
      fulfilledBy: response.fulfilledBy || null,
      availability: response.availability || null,
      brand: response.brand || null
    };

    document.getElementById('readBtn').textContent = 'Sending to backend...';
    
    try {
      const apiResponse = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(productData)
      });

      if (apiResponse.ok) {
        const result = await apiResponse.json();
        html += `<div class="success" style="margin-top: 15px; padding: 10px; background: #4caf50; color: white; border-radius: 5px;">✓ Product data sent successfully!</div>`;
        if (result.message) {
          html += `<div class="product-detail" style="margin-top: 10px;">${result.message}</div>`;
        }
        infoDiv.innerHTML = html;
      } else {
        html += `<div class="error" style="margin-top: 15px; padding: 10px; background: #f44336; color: white; border-radius: 5px;">✗ Failed to send data. Status: ${apiResponse.status}</div>`;
        infoDiv.innerHTML = html;
      }
    } catch (error) {
      html += `<div class="error" style="margin-top: 15px; padding: 10px; background: #f44336; color: white; border-radius: 5px;">✗ Error: ${error.message}. Make sure the backend server is running.</div>`;
      infoDiv.innerHTML = html;
    }

    document.getElementById('readBtn').disabled = false;
    document.getElementById('readBtn').textContent = 'Analyze Product';
  });
});
