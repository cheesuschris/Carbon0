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

function extractProductInfo() {
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
    sellerInfoFound: false
  };

  const titleElement = document.querySelector('#productTitle') ||
                      document.querySelector('h1.a-size-large') ||
                      document.querySelector('h1 span#productTitle') ||
                      document.querySelector('[data-feature-name="title"]');
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
          const fractionText = fraction.textContent.trim();
          priceText += '.' + fractionText;
        }
      } else {
        priceText = priceContainer.textContent.trim();
      }
    }
  }
  
  if (!priceText) {
    const kindlePrice = Array.from(document.querySelectorAll('*')).find(el => {
      const text = el.textContent || '';
      return text.includes('Kindle') && text.match(/\$\d+\.\d{2}/);
    });
    if (kindlePrice) {
      const match = kindlePrice.textContent.match(/\$(\d+\.\d{2})/);
      if (match) {
        priceText = '$' + match[1];
      }
    }
  }
  
  if (!priceText) {
    const allText = document.body.textContent || '';
    const priceMatch = allText.match(/\$\s*(\d+\.\d{2})/);
    if (priceMatch && parseFloat(priceMatch[1]) > 0 && parseFloat(priceMatch[1]) < 10000) {
      priceText = '$' + priceMatch[1];
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
                       document.querySelector('span.a-icon-alt') ||
                       document.querySelector('[data-hook="rating-out-of-text"]');
  if (ratingElement) {
    const ratingText = ratingElement.textContent.trim();
    if (ratingText && (ratingText.includes('out of') || ratingText.match(/\d+\.?\d*\s*out\s*of/)) && ratingText.length < 100) {
      info.rating = ratingText;
    }
  }

  const imageElement = document.querySelector('#landingImage') || 
                       document.querySelector('#imgBlkFront') ||
                       document.querySelector('#main-image') ||
                       document.querySelector('img[data-old-src]') ||
                       document.querySelector('#imageBlock_feature_div img');
  if (imageElement) {
    const imgSrc = imageElement.src || imageElement.getAttribute('data-src') || imageElement.getAttribute('data-old-src');
    if (imgSrc && imgSrc.startsWith('http')) {
      info.image = imgSrc;
    }
  }

  function isValidSeller(sellerName) {
    if (!sellerName || sellerName.length < 2) return false;
    const lowerName = sellerName.toLowerCase();
    const invalidPatterns = [
      'self-publish',
      'author',
      'publisher',
      'by ',
      'visit the',
      'see all',
      'kindle',
      'edition'
    ];
    return !invalidPatterns.some(pattern => lowerName.includes(pattern));
  }

  const merchantInfo = document.querySelector('#merchant-info');
  if (merchantInfo) {
    const merchantText = merchantInfo.textContent.trim();
    const cleanMerchant = cleanText(merchantText);
    if (cleanMerchant && cleanMerchant.length < 200 && isValidSeller(cleanMerchant)) {
      info.soldBy = cleanMerchant;
    }
  }

  const sellerLink = document.querySelector('#sellerProfileTriggerId') ||
                     document.querySelector('a[href*="/gp/help/seller"]') ||
                     document.querySelector('a[href*="/seller"]');
  if (sellerLink && sellerLink.textContent) {
    const sellerText = sellerLink.textContent.trim();
    const cleanSeller = cleanText(sellerText);
    if (cleanSeller && cleanSeller.length < 200 && isValidSeller(cleanSeller)) {
      info.seller = cleanSeller;
    }
  }
  
  if (!info.soldBy && !info.seller) {
    const buyboxArea = document.querySelector('#buybox') || 
                       document.querySelector('#rightCol') ||
                       document.querySelector('[data-feature-name="buybox"]');
    
    if (buyboxArea) {
      const sellerElements = Array.from(buyboxArea.querySelectorAll('a, span, div')).filter(el => {
        const text = (el.textContent || '').trim();
        return (text.includes('Sold by') || text.includes('sold by')) && 
               !text.includes('Author') && 
               !text.includes('Publisher') &&
               !text.includes('Self-Publish');
      });
      
      for (const el of sellerElements) {
        const text = el.textContent.trim();
        const match = text.match(/(?:Sold by|sold by)\s*([^\n\r]+)/i);
        if (match && match[1]) {
          const sellerName = match[1].trim().split(/[\n\r,]/)[0].trim();
          const cleanName = cleanText(sellerName);
          if (cleanName && cleanName.length < 200 && isValidSeller(cleanName)) {
            info.soldBy = cleanName;
            break;
          }
        }
      }
    }
  }

  const buyboxSection = document.querySelector('#buybox') || 
                        document.querySelector('#ppd') ||
                        document.querySelector('#rightCol') ||
                        document.querySelector('[data-feature-name="buybox"]');
  
  if (buyboxSection) {
    const allText = buyboxSection.textContent;
    
    const soldByMatch = allText.match(/Sold by[:\s]+([^\n\r.]+)/i);
    if (soldByMatch && soldByMatch[1]) {
      let soldByText = soldByMatch[1].trim().split(/[\n\r]/)[0].trim();
      soldByText = soldByText.replace(/\.$/, '').trim();
      const cleanSoldBy = cleanText(soldByText);
      if (cleanSoldBy && !info.soldBy && isValidSeller(cleanSoldBy)) {
        info.soldBy = cleanSoldBy;
      }
    }
    
    if (!info.soldBy) {
      const soldByMatch2 = allText.match(/and sold by[:\s]+([^\n\r.]+)/i);
      if (soldByMatch2 && soldByMatch2[1]) {
        let soldByText = soldByMatch2[1].trim().split(/[\n\r]/)[0].trim();
        soldByText = soldByText.replace(/\.$/, '').trim();
        const cleanSoldBy = cleanText(soldByText);
        if (cleanSoldBy && isValidSeller(cleanSoldBy)) {
          info.soldBy = cleanSoldBy;
        }
      }
    }
    
    if (!info.soldBy) {
      const shipperSellerMatch = allText.match(/Shipper\s*\/\s*Seller[:\s]+([^\n\r]+)/i);
      if (shipperSellerMatch && shipperSellerMatch[1]) {
        let sellerText = shipperSellerMatch[1].trim().split(/[\n\r]/)[0].trim();
        sellerText = sellerText.replace(/\.$/, '').trim();
        const cleanSeller = cleanText(sellerText);
        if (cleanSeller && cleanSeller.length < 200) {
          info.soldBy = cleanSeller;
        }
      }
    }

    const fulfilledMatch = allText.match(/Fulfilled by[:\s]+([^\n\r.]+)/i);
    if (fulfilledMatch && fulfilledMatch[1]) {
      let fulfilledText = fulfilledMatch[1].trim().split(/[\n\r]/)[0].trim();
      fulfilledText = fulfilledText.replace(/\.$/, '').trim();
      const cleanFulfilled = cleanText(fulfilledText);
      if (cleanFulfilled && cleanFulfilled.length < 200) {
        info.fulfilledBy = cleanFulfilled;
      }
    }

    if (!info.shipsFrom) {
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
  }

  const offerDisplay = document.querySelector('#offerDisplay_feature_div') ||
                       document.querySelector('[data-feature-name="offerDisplay"]') ||
                       document.querySelector('#olp_feature_div');
  if (offerDisplay && !info.soldBy) {
    const offerText = offerDisplay.textContent;
    const soldByMatch = offerText.match(/Sold by[:\s]+([^\n\r]+)/i);
    if (soldByMatch && soldByMatch[1]) {
      const soldByText = soldByMatch[1].trim().split(/[\n\r]/)[0].trim();
      const cleanSoldBy = cleanText(soldByText);
      if (cleanSoldBy && cleanSoldBy.length < 200 && isValidSeller(cleanSoldBy)) {
        info.soldBy = cleanSoldBy;
      }
    }
  }
  
  if (!info.soldBy) {
    const rightCol = document.querySelector('#rightCol') || 
                     document.querySelector('#buybox') ||
                     document.querySelector('[data-feature-name="buybox"]');
    if (rightCol) {
      const rightColText = rightCol.textContent || '';
      const soldByMatch = rightColText.match(/Sold by[:\s]+([^\n\r]+)/i);
      if (soldByMatch && soldByMatch[1]) {
        const soldByText = soldByMatch[1].trim().split(/[\n\r]/)[0].trim();
        const cleanSoldBy = cleanText(soldByText);
        if (cleanSoldBy && cleanSoldBy.length < 200 && isValidSeller(cleanSoldBy)) {
          info.soldBy = cleanSoldBy;
        }
      }
      
      if (!info.fulfilledBy) {
        const fulfilledMatch = rightColText.match(/Fulfilled by[:\s]+([^\n\r]+)/i);
        if (fulfilledMatch && fulfilledMatch[1]) {
          const fulfilledText = fulfilledMatch[1].trim().split(/[\n\r]/)[0].trim();
          const cleanFulfilled = cleanText(fulfilledText);
          if (cleanFulfilled && cleanFulfilled.length < 200) {
            info.fulfilledBy = cleanFulfilled;
          }
        }
      }
      
      if (!info.shipsFrom) {
        const shipsMatch = rightColText.match(/Ships from[:\s]+([^\n\r.]+)/i);
        if (shipsMatch && shipsMatch[1]) {
          let shipsText = shipsMatch[1].trim();
          shipsText = shipsText.split(/[\n\r]/)[0].trim();
          shipsText = shipsText.split(/and sold by/i)[0].trim();
          shipsText = shipsText.replace(/\.$/, '').trim();
          const cleanShips = cleanText(shipsText);
          if (cleanShips && cleanShips.length < 200) {
            info.shipsFrom = cleanShips;
          }
        }
      }
      
      if (!info.soldBy) {
        const soldByMatch = rightColText.match(/sold by[:\s]+([^\n\r.]+)/i);
        if (soldByMatch && soldByMatch[1]) {
          let soldByText = soldByMatch[1].trim();
          soldByText = soldByText.split(/[\n\r]/)[0].trim();
          soldByText = soldByText.replace(/\.$/, '').trim();
          const cleanSoldBy = cleanText(soldByText);
          if (cleanSoldBy && cleanSoldBy.length < 200) {
            info.soldBy = cleanSoldBy;
          }
        }
      }
      
      if (!info.soldBy) {
        const shipperSellerMatch = rightColText.match(/Shipper\s*\/\s*Seller[:\s]+([^\n\r]+)/i);
        if (shipperSellerMatch && shipperSellerMatch[1]) {
          let sellerText = shipperSellerMatch[1].trim();
          sellerText = sellerText.split(/[\n\r]/)[0].trim();
          sellerText = sellerText.replace(/\.$/, '').trim();
          const cleanSeller = cleanText(sellerText);
          if (cleanSeller && cleanSeller.length < 200) {
            info.soldBy = cleanSeller;
          }
        }
      }
    }
  }
  
  if (!info.fulfilledBy) {
    const fulfilledElements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.textContent || '').trim();
      return text.includes('Fulfilled by') && !text.includes('Amazon.com');
    });
    for (const el of fulfilledElements) {
      const text = el.textContent.trim();
      const match = text.match(/Fulfilled by[:\s]+([^\n\r]+)/i);
      if (match && match[1]) {
        const fulfilledText = match[1].trim().split(/[\n\r]/)[0].trim();
        const cleanFulfilled = cleanText(fulfilledText);
        if (cleanFulfilled && cleanFulfilled.length < 200) {
          info.fulfilledBy = cleanFulfilled;
          break;
        }
      }
    }
  }
  
  if (!info.soldBy) {
    const shipperSellerElements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.textContent || '').trim();
      return text.includes('Shipper') && text.includes('Seller');
    });
    for (const el of shipperSellerElements) {
      const text = el.textContent.trim();
      const match = text.match(/Shipper\s*\/\s*Seller[:\s]+([^\n\r]+)/i);
      if (match && match[1]) {
        let sellerText = match[1].trim().split(/[\n\r]/)[0].trim();
        sellerText = sellerText.replace(/\.$/, '').trim();
        const cleanSeller = cleanText(sellerText);
        if (cleanSeller && cleanSeller.length < 200) {
          info.soldBy = cleanSeller;
          break;
        }
      }
    }
  }
  
  if (!info.shipsFrom) {
    const shipsElements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.textContent || '').trim();
      return text.includes('Ships from') || text.includes('ships from');
    });
    for (const el of shipsElements) {
      const text = el.textContent.trim();
      const match = text.match(/Ships from[:\s]+([^\n\r.]+)/i);
      if (match && match[1]) {
        let shipsText = match[1].trim().split(/[\n\r]/)[0].trim();
        shipsText = shipsText.split(/and sold by/i)[0].trim();
        shipsText = shipsText.replace(/\.$/, '').trim();
        const cleanShips = cleanText(shipsText);
        if (cleanShips && cleanShips.length < 200) {
          info.shipsFrom = cleanShips;
          break;
        }
      }
    }
  }

  const availabilityElement = document.querySelector('#availability span') ||
                             document.querySelector('#availability');
  if (availabilityElement) {
    const availText = availabilityElement.textContent.trim();
    const cleanAvail = cleanText(availText);
    if (cleanAvail && availText.length < 100) {
      info.availability = cleanAvail;
    }
  }

  const brandElement = document.querySelector('#brand') || 
                      document.querySelector('#bylineInfo') ||
                      document.querySelector('a[href*="/s?k="]') ||
                      document.querySelector('.po-brand .po-break-word');
  if (brandElement) {
    let brandText = brandElement.textContent.trim();
    if (brandText.includes('Visit the')) {
      brandText = brandText.replace(/Visit the\s+/i, '').trim();
    }
    if (brandText.includes('Brand:')) {
      brandText = brandText.replace(/Brand:\s*/i, '').trim();
    }
    const cleanBrand = cleanText(brandText);
    if (cleanBrand && brandText.length < 200 && !brandText.includes('See all')) {
      info.brand = cleanBrand;
    }
  }
  
  if (!info.brand) {
    const bylineInfo = document.querySelector('#bylineInfo');
    if (bylineInfo) {
      const bylineText = bylineInfo.textContent.trim();
      if (bylineText && !bylineText.includes('by') && bylineText.length < 200) {
        const cleanByline = cleanText(bylineText);
        if (cleanByline) {
          info.brand = cleanByline;
        }
      }
    }
  }

  const bylineInfo = document.querySelector('#bylineInfo');
  if (bylineInfo) {
    const bylineText = bylineInfo.textContent.trim();
    if (bylineText && bylineText.includes('by')) {
      let authorsText = bylineText.replace(/^by\s+/i, '').trim();
      authorsText = authorsText.replace(/\s*\(Author\)/gi, '');
      authorsText = authorsText.replace(/\s*\(Author\),\s*/gi, ', ');
      authorsText = authorsText.replace(/\s*&\s*\d+\s*more/gi, '');
      authorsText = authorsText.replace(/\s*,\s*&\s*/gi, ', ');
      const cleanAuthors = cleanText(authorsText);
      if (cleanAuthors && cleanAuthors.length < 500 && cleanAuthors.length > 2) {
        info.authors = cleanAuthors;
      }
    }
  }

  if (!info.authors) {
    const authorLinks = Array.from(document.querySelectorAll('a[href*="/e/"]')).filter(link => {
      const text = link.textContent.trim();
      const href = link.getAttribute('href') || '';
      return text && text.length > 2 && text.length < 100 && 
             href.includes('/e/') && 
             !text.includes('See all') && 
             !text.includes('Visit the') &&
             !text.match(/^\d+$/);
    });
    if (authorLinks.length > 0) {
      const authorsList = authorLinks.map(link => link.textContent.trim()).filter((name, index, self) => {
        return name && self.indexOf(name) === index;
      });
      if (authorsList.length > 0) {
        info.authors = authorsList.join(', ');
      }
    }
  }
  
  if (!info.authors) {
    const contributorSection = document.querySelector('[data-contributor-name]') ||
                               document.querySelector('.contributorNameID');
    if (contributorSection) {
      const contributorLinks = Array.from(contributorSection.querySelectorAll('a')).filter(link => {
        const text = link.textContent.trim();
        return text && text.length > 2 && text.length < 100;
      });
      if (contributorLinks.length > 0) {
        const authorsList = contributorLinks.map(link => link.textContent.trim());
        if (authorsList.length > 0) {
          info.authors = authorsList.join(', ');
        }
      }
    }
  }

  if (!info.authors) {
    const contributorElements = document.querySelectorAll('[data-contributor-name]');
    if (contributorElements.length > 0) {
      const authorsList = Array.from(contributorElements).map(el => {
        return el.getAttribute('data-contributor-name') || el.textContent.trim();
      }).filter(name => name && name.length > 0);
      if (authorsList.length > 0) {
        info.authors = authorsList.join(', ');
      }
    }
  }

  info.sellerInfoFound = !!(info.soldBy || info.seller || info.fulfilledBy || info.shipsFrom);

  return info;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getProductInfo') {
    const productInfo = extractProductInfo();
    sendResponse(productInfo);
  }
  return true;
});


