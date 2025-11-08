const API_URL = 'http://localhost:5000/api/product';

document.getElementById('readBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  const supportedPlatforms = ['amazon.com', 'walmart.com', 'etsy.com', 'bestbuy.com', 'target.com', 'ebay.com'];
  const isSupported = supportedPlatforms.some(platform => tab.url.includes(platform));
  
  document.getElementById('productInfo').classList.add('show');
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
      document.getElementById('readBtn').textContent = "Analyze This Product's Carbon Footprint!";
      return;
    }

    const hasAnyData = response.title || response.price || response.rating || response.image;
    if (!hasAnyData) {
      infoDiv.innerHTML = '<div class="error">Could not extract product information. The page structure may have changed.</div>';
      document.getElementById('readBtn').disabled = false;
      document.getElementById('readBtn').textContent = "Analyze This Product's Carbon Footprint!";
      return;
    }

    let html = '';
    html += `<div class="header">Product Description:</div>`
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
    } catch (error) {
      html += `<div class="error" style="margin-top: 15px; padding: 10px; background: #f44336; color: white; border-radius: 5px;">Error: ${error.message}. Make sure the backend server is running.</div>`;
      infoDiv.innerHTML = html;
    }

    document.getElementById('productAnalysis').classList.add('show');
    document.getElementById('productAnalysis').innerHTML = '<div class="loading">Analyzing extracted information...</div>';
    const analysisDiv = document.getElementById('productAnalysis');
    let analysis = ``;
    if (!apiResponse.ok) {
      analysis += `<div class="product-detail">Backend Failed: ${apiResponse.status} error}</div>`
      analysisDiv.innerHTML = analysis;
      return;
    }
    const data = await apiResponse.json();
    analysis += `<div class="header">Carbon0 Score: ${data.C0Score}</div>`
    if (data.C0Score < data.link1C0Score && data.C0Score < data.link2C0Score && data.C0Score < data.link3C0Score && data.C0Score < data.link4C0Score && data.C0Score < data.link5C0Score) {
      analysis += `<div class="product-detail">Hooray! This product already has the lowest C0Score among similar products. Feel free to still check them out:</div>`
    } else {
      analysis += `<div class="product-detail">We found some better alternatives! Check them out here:</div>`
    }
    analysis += `<div class="product-detail">
                   <ol>
                    <li>
                      ${data.link1} - Carbon0 Score: ${data.link1C0Score}
                      <img src="${data.link1Image}" alt="Suggested alternative 1 image">
                      <button onclick="this.parentElement.querySelector('.explanation').classList.toggle('show')">Pros/Cons Analysis</button>
                      <button>Add to KnotCart</button>
                      <div class="explanation">
                        ${data.link1Explanation}
                      </div>
                    </li>
                    <li>
                      ${data.link2} - Carbon0 Score: ${data.link2C0Score}
                      <img src="${data.link2Image}" alt="Suggested alternative 2 image">
                      <button onclick="this.parentElement.querySelector('.explanation').classList.toggle('show')">Pros/Cons Analysis</button>
                      <button>Add to KnotCart</button>
                      <div class="explanation">
                        ${data.link2Explanation}
                      </div>
                    </li>
                    <li>
                      ${data.link3} - Carbon0 Score: ${data.link3C0Score}
                      <img src="${data.link3Image}" alt="Suggested alternative 3 image">
                      <button onclick="this.parentElement.querySelector('.explanation').classList.toggle('show')">Pros/Cons Analysis</button>
                      <button>Add to KnotCart</button>
                      <div class="explanation">
                        ${data.link3Explanation}
                      </div>
                    </li>
                    <li>
                      ${data.link4} - Carbon0 Score: ${data.link4C0Score}
                      <img src="${data.link4Image}" alt="Suggested alternative 4 image">
                      <button onclick="this.parentElement.querySelector('.explanation').classList.toggle('show')">Pros/Cons Analysis</button>
                      <button>Add to KnotCart</button>
                      <div class="explanation">
                        ${data.link4Explanation}
                      </div>
                    </li>
                    <li>
                      ${data.link5} - Carbon0 Score: ${data.link5C0Score}
                      <img src="${data.link5Image}" alt="Suggested alternative 5 image">
                      <button onclick="this.parentElement.querySelector('.explanation').classList.toggle('show')">Pros/Cons Analysis</button>
                      <button>Add to KnotCart</button>
                      <div class="explanation">
                        ${data.link5Explanation}
                      </div>
                    </li>
                   </ol>
                 </div>`
    analysis += `<button class="header">Knot Checkout</div>`
    analysisDiv.innerHTML = analysis;
    
    document.getElementById('readBtn').disabled = false;
    document.getElementById('readBtn').textContent = "Analyze This Product's Carbon Footprint!";
  });
});
