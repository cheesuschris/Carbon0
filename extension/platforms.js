function cleanText(text) {
  if (!text) return null;
  text = text.trim();
  if (text.length > 500) return null;
  if (text.includes('typeof') || text.includes('function()') || text.includes('csa(') || text.includes('AUI_')) {
    return null;
  }
  if (text.startsWith('{') && text.includes('"AUI_')) {
    return null;
  }
  return text;
}

function detectPlatform(url) {
  if (url.includes('amazon.com')) return 'Amazon';
  if (url.includes('walmart.com')) return 'Walmart';
  if (url.includes('etsy.com')) return 'Etsy';
  if (url.includes('bestbuy.com')) return 'Best Buy';
  if (url.includes('target.com')) return 'Target';
  if (url.includes('ebay.com')) return 'eBay';
  return 'Unknown';
}

function extractAmazon() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    authors: null,
    reviews: []
  };

  const titleElement = document.querySelector('#productTitle') ||
                      document.querySelector('h1.a-size-large') ||
                      document.querySelector('h1 span#productTitle');
  if (titleElement) {
    const titleText = titleElement.textContent.trim();
    if (titleText && titleText.length > 0 && titleText.length < 500) {
      info.title = titleText;
    }
  }

  let priceText = null;
  const offscreenPrice = document.querySelector('.a-price .a-offscreen');
  if (offscreenPrice) {
    priceText = offscreenPrice.textContent.trim();
  }
  if (!priceText) {
    const priceBlock = document.querySelector('#priceblock_ourprice') ||
                       document.querySelector('#priceblock_dealprice') ||
                       document.querySelector('#priceblock_saleprice');
    if (priceBlock) {
      priceText = priceBlock.textContent.trim();
    }
  }
  if (!priceText) {
    const priceContainer = document.querySelector('.a-price') || 
                          document.querySelector('span.a-price');
    if (priceContainer) {
      const symbol = priceContainer.querySelector('.a-price-symbol');
      const whole = priceContainer.querySelector('.a-price-whole');
      const fraction = priceContainer.querySelector('.a-price-fraction');
      if (symbol && whole) {
        const wholeText = whole.textContent.trim().replace(/\./g, '');
        priceText = (symbol.textContent || '$') + wholeText;
        if (fraction) {
          priceText += '.' + fraction.textContent.trim();
        }
      }
    }
  }
  if (priceText) {
    priceText = priceText.replace(/\.\.+/g, '.').replace(/\s+/g, '');
    if (cleanText(priceText) && priceText.length < 50 && priceText.match(/^\$?\d+\.?\d{0,2}$/)) {
      if (!priceText.startsWith('$')) {
        priceText = '$' + priceText;
      }
      info.price = priceText;
    }
  }

  const ratingElement = document.querySelector('#acrPopover span.a-icon-alt') ||
                       document.querySelector('span.a-icon-alt');
  if (ratingElement) {
    const ratingText = ratingElement.textContent.trim();
    if (ratingText && (ratingText.includes('out of') || ratingText.match(/\d+\.?\d*\s*out\s*of/)) && ratingText.length < 100) {
      info.rating = ratingText;
    }
  }

  const imageElement = document.querySelector('#landingImage') || 
                       document.querySelector('#imgBlkFront') ||
                       document.querySelector('#main-image');
  if (imageElement) {
    const imgSrc = imageElement.src || imageElement.getAttribute('data-src') || imageElement.getAttribute('data-old-src');
    if (imgSrc && imgSrc.startsWith('http')) {
      info.image = imgSrc;
    }
  }

  const buyboxSection = document.querySelector('#buybox') || 
                        document.querySelector('#rightCol') ||
                        document.querySelector('[data-feature-name="buybox"]');
  if (buyboxSection) {
    const allText = buyboxSection.textContent;
    const shipperSellerMatch = allText.match(/Shipper\s*\/\s*Seller[:\s]+([^\n\r]+)/i);
    if (shipperSellerMatch && shipperSellerMatch[1]) {
      let sellerText = shipperSellerMatch[1].trim().split(/[\n\r]/)[0].trim();
      sellerText = sellerText.replace(/\.$/, '').trim();
      const cleanSeller = cleanText(sellerText);
      if (cleanSeller && cleanSeller.length < 200) {
        info.soldBy = cleanSeller;
      }
    }
    const shipsMatch = allText.match(/Ships from[:\s]+([^\n\r.]+)/i);
    if (shipsMatch && shipsMatch[1]) {
      let shipsText = shipsMatch[1].trim().split(/[\n\r]/)[0].trim();
      shipsText = shipsText.split(/and sold by/i)[0].trim();
      shipsText = shipsText.replace(/\.$/, '').trim();
      const cleanShips = cleanText(shipsText);
      if (cleanShips && cleanShips.length < 200) {
        info.shipsFrom = cleanShips;
      }
    }
  }

  const reviewElements = Array.from(document.querySelectorAll('[data-hook="review"]')).slice(0, 3);
  reviewElements.forEach(review => {
    const reviewText = review.querySelector('[data-hook="review-body"]');
    if (reviewText) {
      const text = reviewText.textContent.trim();
      if (text && text.length > 10) {
        info.reviews.push(text.substring(0, 500));
      }
    }
  });

  return info;
}

function extractWalmart() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  const titleElement = document.querySelector('h1[itemprop="name"]') ||
                      document.querySelector('h1.prod-ProductTitle');
  if (titleElement) {
    info.title = titleElement.textContent.trim();
  }

  const priceElement = document.querySelector('[itemprop="price"]') ||
                      document.querySelector('.price-current') ||
                      document.querySelector('[data-testid="product-price"]');
  if (priceElement) {
    const priceText = priceElement.textContent.trim();
    if (priceText && priceText.length < 50) {
      info.price = priceText;
    }
  }

  const ratingElement = document.querySelector('[itemprop="ratingValue"]') ||
                      document.querySelector('.stars-reviews');
  if (ratingElement) {
    const ratingText = ratingElement.textContent.trim();
    if (ratingText && ratingText.length < 50) {
      info.rating = ratingText;
    }
  }

  const imageElement = document.querySelector('[itemprop="image"]') ||
                      document.querySelector('img[data-testid="product-image"]');
  if (imageElement) {
    info.image = imageElement.src || imageElement.getAttribute('data-src');
  }

  const sellerElement = document.querySelector('[data-testid="seller-name"]');
  if (sellerElement) {
    info.soldBy = sellerElement.textContent.trim();
  }

  const reviewElements = Array.from(document.querySelectorAll('[data-testid="review"]')).slice(0, 3);
  reviewElements.forEach(review => {
    const reviewText = review.querySelector('[data-testid="review-text"]');
    if (reviewText) {
      const text = reviewText.textContent.trim();
      if (text && text.length > 10) {
        info.reviews.push(text.substring(0, 500));
      }
    }
  });

  return info;
}

function extractEtsy() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  const titleElement = document.querySelector('h1[data-buy-box-listing-title]') ||
                      document.querySelector('h1.wt-text-body-01');
  if (titleElement) {
    info.title = titleElement.textContent.trim();
  }

  const priceElement = document.querySelector('.wt-text-title-03 .currency-value') ||
                      document.querySelector('[data-buy-box-region] .currency-value');
  if (priceElement) {
    const priceText = priceElement.textContent.trim();
    const currency = document.querySelector('.currency-symbol')?.textContent || '$';
    if (priceText) {
      info.price = currency + priceText;
    }
  }

  let ratingElement = document.querySelector('[data-rating]');
  if (ratingElement) {
    const rating = ratingElement.getAttribute('data-rating');
    if (rating && rating !== '0') {
      info.rating = rating + ' out of 5 stars';
    }
  }
  
  if (!info.rating) {
    ratingElement = document.querySelector('.wt-text-body-01 .wt-display-inline-block');
    if (ratingElement) {
      const ratingText = ratingElement.textContent.trim();
      const ratingMatch = ratingText.match(/(\d+\.?\d*)\s*(?:out of|\/)\s*5/);
      if (ratingMatch && ratingMatch[1]) {
        info.rating = ratingMatch[1] + ' out of 5 stars';
      }
    }
  }
  
  if (!info.rating) {
    const starElements = Array.from(document.querySelectorAll('[class*="star"]')).find(el => {
      const text = el.textContent || '';
      return text.match(/\d+\.?\d*\s*(?:out of|\/)\s*5/);
    });
    if (starElements) {
      const ratingText = starElements.textContent.trim();
      const ratingMatch = ratingText.match(/(\d+\.?\d*)\s*(?:out of|\/)\s*5/);
      if (ratingMatch && ratingMatch[1]) {
        info.rating = ratingMatch[1] + ' out of 5 stars';
      }
    }
  }
  
  if (!info.rating) {
    const allText = document.body.textContent || '';
    const ratingMatch = allText.match(/(\d+\.?\d*)\s*(?:out of|\/)\s*5\s*stars?/i);
    if (ratingMatch && ratingMatch[1] && parseFloat(ratingMatch[1]) > 0) {
      info.rating = ratingMatch[1] + ' out of 5 stars';
    }
  }

  const imageElement = document.querySelector('#image-carousel img') ||
                      document.querySelector('.wt-max-width-full img');
  if (imageElement) {
    info.image = imageElement.src || imageElement.getAttribute('data-src');
  }

  const sellerElement = document.querySelector('a[href*="/shop/"]');
  if (sellerElement) {
    info.soldBy = sellerElement.textContent.trim();
  }

  const shipsFromElement = document.querySelector('[data-shipping-from]');
  if (shipsFromElement) {
    info.shipsFrom = shipsFromElement.getAttribute('data-shipping-from') || shipsFromElement.textContent.trim();
  }

  const reviewElements = Array.from(document.querySelectorAll('.review-item')).slice(0, 3);
  reviewElements.forEach(review => {
    const reviewText = review.querySelector('.review-text');
    if (reviewText) {
      const text = reviewText.textContent.trim();
      if (text && text.length > 10) {
        info.reviews.push(text.substring(0, 500));
      }
    }
  });

  return info;
}

function extractBestBuy() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  const titleElement = document.querySelector('h1.heading-5') ||
                      document.querySelector('[data-testid="product-title"]') ||
                      document.querySelector('h1.sr-only') ||
                      document.querySelector('h1[class*="heading"]') ||
                      document.querySelector('h1');
  if (titleElement) {
    const titleText = titleElement.textContent.trim();
    if (titleText && titleText.length > 0) {
      info.title = titleText;
    }
  }

  const priceElement = document.querySelector('.priceView-customer-price span') ||
                      document.querySelector('[data-testid="customer-price"]') ||
                      document.querySelector('.priceView-customer-price') ||
                      document.querySelector('[class*="price"]') ||
                      document.querySelector('[data-testid*="price"]');
  if (priceElement) {
    const priceText = priceElement.textContent.trim();
    if (priceText && priceText.length < 50 && priceText.match(/[\$£€¥]\s*\d+/)) {
      info.price = priceText;
    }
  }

  let ratingElement = document.querySelector('[data-testid="rating"]') ||
                      document.querySelector('[data-rating]') ||
                      document.querySelector('.rating-value');
  if (ratingElement) {
    const rating = ratingElement.getAttribute('data-rating') || 
                   ratingElement.getAttribute('data-testid') ||
                   ratingElement.textContent.trim();
    if (rating && rating.length < 50) {
      info.rating = rating;
    }
  }
  
  if (!info.rating) {
    const ratingText = document.body.textContent || '';
    const ratingMatch = ratingText.match(/(\d+\.?\d*)\s*(?:out of|\/)\s*5/);
    if (ratingMatch && ratingMatch[1]) {
      info.rating = ratingMatch[1] + ' out of 5 stars';
    }
  }

  const imageElement = document.querySelector('.primary-image img') ||
                      document.querySelector('[data-testid="product-image"] img') ||
                      document.querySelector('img[alt*="product"]') ||
                      document.querySelector('.product-image img') ||
                      document.querySelector('img[src*="bbystatic"]');
  if (imageElement) {
    const imgSrc = imageElement.src || imageElement.getAttribute('data-src') || imageElement.getAttribute('srcset');
    if (imgSrc && imgSrc.startsWith('http')) {
      info.image = imgSrc.split(' ')[0];
    }
  }

  info.soldBy = 'Best Buy';

  const reviewElements = Array.from(document.querySelectorAll('.review-item, [data-testid*="review"]')).slice(0, 3);
  reviewElements.forEach(review => {
    const reviewText = review.querySelector('.review-text, [data-testid*="review-text"]');
    if (reviewText) {
      const text = reviewText.textContent.trim();
      if (text && text.length > 10) {
        info.reviews.push(text.substring(0, 500));
      }
    }
  });

  return info;
}

function extractTarget() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  const titleElement = document.querySelector('h1[data-test="product-title"]') ||
                      document.querySelector('h1');
  if (titleElement) {
    info.title = titleElement.textContent.trim();
  }

  const priceElement = document.querySelector('[data-test="product-price"]') ||
                      document.querySelector('.h-padding-r-tiny');
  if (priceElement) {
    info.price = priceElement.textContent.trim();
  }

  const ratingElement = document.querySelector('[data-test="rating"]');
  if (ratingElement) {
    info.rating = ratingElement.textContent.trim();
  }

  const imageElement = document.querySelector('[data-test="product-image"] img') ||
                      document.querySelector('img[alt*="product"]');
  if (imageElement) {
    info.image = imageElement.src || imageElement.getAttribute('data-src');
  }

  info.soldBy = 'Target';

  const reviewElements = Array.from(document.querySelectorAll('[data-test="review"]')).slice(0, 3);
  reviewElements.forEach(review => {
    const reviewText = review.querySelector('[data-test="review-text"]');
    if (reviewText) {
      const text = reviewText.textContent.trim();
      if (text && text.length > 10) {
        info.reviews.push(text.substring(0, 500));
      }
    }
  });

  return info;
}

function extractEbay() {
  const info = {
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  const titleElement = document.querySelector('h1[itemprop="name"]') ||
                      document.querySelector('#x-item-title-label');
  if (titleElement) {
    info.title = titleElement.textContent.trim();
  }

  const priceElement = document.querySelector('[itemprop="price"]') ||
                      document.querySelector('.notranslate');
  if (priceElement) {
    const priceText = priceElement.textContent.trim();
    if (priceText && priceText.length < 50) {
      info.price = priceText;
    }
  }

  const imageElement = document.querySelector('#icImg') ||
                      document.querySelector('[itemprop="image"]');
  if (imageElement) {
    info.image = imageElement.src || imageElement.getAttribute('data-src');
  }

  const sellerElement = document.querySelector('.mbg-nw a');
  if (sellerElement) {
    info.soldBy = sellerElement.textContent.trim();
  }

  const shipsFromElement = document.querySelector('[data-testid="ux-labels-values"]');
  if (shipsFromElement) {
    const text = shipsFromElement.textContent;
    const match = text.match(/Ships from[:\s]+([^\n]+)/i);
    if (match) {
      info.shipsFrom = match[1].trim();
    }
  }

  return info;
}

function extractProductInfo() {
  const url = window.location.href;
  const platform = detectPlatform(url);
  
  let productInfo = {
    platform: platform,
    url: url,
    title: null,
    price: null,
    rating: null,
    image: null,
    seller: null,
    shipsFrom: null,
    soldBy: null,
    fulfilledBy: null,
    availability: null,
    brand: null,
    reviews: []
  };

  switch (platform) {
    case 'Amazon':
      productInfo = { ...productInfo, ...extractAmazon() };
      break;
    case 'Walmart':
      productInfo = { ...productInfo, ...extractWalmart() };
      break;
    case 'Etsy':
      productInfo = { ...productInfo, ...extractEtsy() };
      break;
    case 'Best Buy':
      productInfo = { ...productInfo, ...extractBestBuy() };
      break;
    case 'Target':
      productInfo = { ...productInfo, ...extractTarget() };
      break;
    case 'eBay':
      productInfo = { ...productInfo, ...extractEbay() };
      break;
    default:
      break;
  }

  return productInfo;
}

