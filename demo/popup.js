document.getElementById('readBtn').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab.url.includes('amazon.com')) {
    document.getElementById('productInfo').innerHTML = 
      '<div class="error">Please navigate to an Amazon product page</div>';
    return;
  }

  chrome.tabs.sendMessage(tab.id, { action: 'getProductInfo' }, (response) => {
    const infoDiv = document.getElementById('productInfo');
    
    if (!response) {
      infoDiv.innerHTML = '<div class="error">Could not extract product information. Make sure you are on an Amazon product page.</div>';
      return;
    }

    const hasAnyData = response.title || response.price || response.rating || response.seller || response.soldBy || response.brand || response.availability;
    if (!hasAnyData) {
      infoDiv.innerHTML = '<div class="error">Could not extract product information. The page structure may have changed.</div>';
      return;
    }

    let html = '';
    if (response.title) {
      html += `<div class="product-title">${response.title}</div>`;
    }
    if (response.authors) {
      html += `<div class="product-detail"><strong>Authors:</strong> ${response.authors}</div>`;
    }
    if (response.brand) {
      html += `<div class="product-detail"><strong>Brand:</strong> ${response.brand}</div>`;
    }
    if (response.price) {
      html += `<div class="product-detail"><strong>Price:</strong> ${response.price}</div>`;
    }
    if (response.rating) {
      html += `<div class="product-detail"><strong>Rating:</strong> ${response.rating}</div>`;
    }
    if (response.availability) {
      html += `<div class="product-detail"><strong>Availability:</strong> ${response.availability}</div>`;
    }
    if (response.soldBy) {
      html += `<div class="product-detail"><strong>Sold By:</strong> ${response.soldBy}</div>`;
    }
    if (response.seller) {
      html += `<div class="product-detail"><strong>Seller:</strong> ${response.seller}</div>`;
    }
    if (response.fulfilledBy) {
      html += `<div class="product-detail"><strong>Fulfilled By:</strong> ${response.fulfilledBy}</div>`;
    }
    if (response.shipsFrom) {
      html += `<div class="product-detail"><strong>Ships From:</strong> ${response.shipsFrom}</div>`;
    }
    if (!response.sellerInfoFound) {
      html += `<div class="product-detail" style="color: #d32f2f; font-style: italic;"><strong>Debug:</strong> No valid seller information found on this page</div>`;
    }
    if (response.image) {
      html += `<div class="product-detail"><img src="${response.image}" style="max-width: 100%; height: auto; margin-top: 10px;" /></div>`;
    }

    infoDiv.innerHTML = html || '<div class="error">No product information found</div>';
  });
});


