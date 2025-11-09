chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Cart content script received message:', request);
  if (request.action === 'addToCart') {
    console.log('Posting message to page:', request.data);
    window.postMessage({
      action: 'addToCart',
      data: request.data
    }, '*');
    sendResponse({ success: true });
  }
  return true;
});

console.log('Cart content script loaded');

