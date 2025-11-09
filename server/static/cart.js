const STORAGE_KEY = 'carbon0_cart';

let cartData = [];

function loadCart() {
  const stored = localStorage.getItem(STORAGE_KEY);
  console.log('Loading cart from localStorage:', stored);
  if (stored) {
    try {
      cartData = JSON.parse(stored);
      console.log('Loaded cart data:', cartData);
    } catch (e) {
      console.error('Failed to parse cart data:', e);
      cartData = [];
    }
  } else {
    cartData = [];
  }
  renderCart();
}

function saveCart() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cartData));
  renderCart();
}

function addToCart(alternative, original) {
  console.log('addToCart called with:', { alternative, original });
  
  if (!alternative || !original) {
    console.error('Missing alternative or original data');
    return;
  }
  
  const existingIndex = cartData.findIndex(item => 
    item.original.url === original.url && 
    item.alternative.url === alternative.url
  );
  
  if (existingIndex >= 0) {
    console.log('Product already in cart');
    return;
  }
  
  cartData.push({
    id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
    alternative: alternative,
    original: original,
    addedAt: new Date().toISOString()
  });
  
  console.log('Cart data after add:', cartData);
  saveCart();
}

function removeFromCart(id) {
  cartData = cartData.filter(item => item.id !== id);
  saveCart();
}

function calculateStats() {
  const totalAlternatives = cartData.length;
  const totalCO2Saved = cartData.reduce((sum, item) => sum + (item.alternative.co2Saved || 0), 0);
  document.getElementById('total-alternatives').textContent = totalAlternatives;
  document.getElementById('total-co2-saved').textContent = totalCO2Saved.toFixed(1) + ' kg';
}

function renderCart() {
  const container = document.getElementById('cart-container');
  
  if (cartData.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <h2>Your cart is empty</h2>
        <p>Start browsing products and add eco-friendly alternatives to see your smart carbon emissions savings!</p>
      </div>
    `;
    calculateStats();
    return;
  }

  const groupedByOriginal = {};
  cartData.forEach(item => {
    const key = item.original.url || item.original.name;
    if (!groupedByOriginal[key]) {
      groupedByOriginal[key] = {
        original: item.original,
        alternatives: []
      };
    }
    groupedByOriginal[key].alternatives.push(item);
  });
  
  let html = '';
  
  Object.values(groupedByOriginal).forEach(group => {
    html += `
      <div class="product-group">
        <div class="original-product">
          <div class="label">Original Product</div>
          <div class="product-name">${group.original.name || 'Product'}</div>
          <div class="product-details">
            ${group.original.price ? `<div class="detail-item"><strong>Price:</strong> ${group.original.price}</div>` : ''}
            ${group.original.platform ? `<div class="detail-item"><strong>Platform:</strong> ${group.original.platform}</div>` : ''}
          </div>
        </div>
        <div class="alternatives-list">
    `;
    
    group.alternatives.forEach(item => {
      const alt = item.alternative;
      html += `
        <div class="alternative-item">
          ${alt.image ? `<img src="${alt.image}" alt="alternative" class="product-image" onerror="this.style.display='none'">` : ''}
          <div class="product-info">
            <div class="product-details">
              ${alt.url ? `<div class="detail-item"><strong>URL:</strong> <a href="${alt.url}" target="_blank">View Product</a></div>` : ''}
              ${alt.C0Score ? `<div class="detail-item"><strong>Price:</strong> ${alt.C0Score}</div>` : ''}
              ${alt.explanation ? `<div class="detail-item"><strong>Merchant:</strong> ${alt.explanation}</div>` : ''}
            </div>
          </div>
          <button class="remove-btn" onclick="removeFromCart('${item.id}')">Remove</button>
        </div>
      `;
    });

    html += `
        </div>
      </div>
    `;
  });
      
  if (cartData.length !== 0) {
    html += `<button class="finish-btn" onclick="finishCheckout()">I've finished checking out all these websites!</button>`
  }
  
  container.innerHTML = html;
  calculateStats();
}

function createConfetti() {
  const colors = ['#4CAF50', '#8BC34A', '#66BB6A', '#81C784', '#A5D6A7'];
  const confettiCount = 100;
  
  for (let i = 0; i < confettiCount; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.left = Math.random() * 100 + '%';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animationDelay = Math.random() * 3 + 's';
    confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
    document.body.appendChild(confetti);
    
    setTimeout(() => confetti.remove(), 5000);
  }
}

async function finishCheckout() {
  const totalCO2Saved = cartData.reduce((sum, item) => {
    return sum + (item.alternative.co2Saved || 0);
  }, 0);
  try {
    const response = await fetch('http://localhost:5000/cart/checkout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ amount: totalCO2Saved })
    });
    const data = await response.json();
    if (response.ok) {
      console.log('Checkout successful:', data);
      createConfetti();
      setTimeout(() => {
        cartData = [];
        saveCart();
      }, 1000);
    } else {
      console.error('Checkout failed:', data.error);
      alert('Failed to complete checkout: ' + data.error);
    }
  } catch (error) {
    console.error('Network error during checkout:', error);
    alert('Network error: ' + error.message);
  }
}

window.finishCheckout = finishCheckout;

window.addEventListener('message', (event) => {
  console.log('Cart page received message:', event.data);
  if (event.data && event.data.action === 'addToCart') {
    console.log('Adding to cart via message:', event.data.data);
    addToCart(event.data.data.alternative, event.data.data.original);
  }
});

if (typeof window.removeFromCart === 'undefined') {
  window.removeFromCart = removeFromCart;
}

function handleUrlProduct() {
  const urlParams = new URLSearchParams(window.location.search);
  const productParam = urlParams.get('product');

  if (productParam) {
    try {
      const productData = JSON.parse(decodeURIComponent(productParam));
      console.log('Adding product from URL:', productData);
      if (productData.alternative && productData.original) {
        addToCart(productData.alternative, productData.original);
        window.history.replaceState({}, '', '/cart');
        return true;
      } else {
        console.error('Invalid product data structure:', productData);
      }
    } catch (e) {
      console.error('Failed to parse product data:', e);
    }
  }
  return false;
}

loadCart();

if (handleUrlProduct()) {
  console.log('Product added from URL parameter');
}

let lastUrl = window.location.href;
setInterval(() => {
  if (window.location.href !== lastUrl) {
    lastUrl = window.location.href;
    if (handleUrlProduct()) {
      console.log('Product added from URL parameter (after navigation)');
    }
  }
}, 500);

