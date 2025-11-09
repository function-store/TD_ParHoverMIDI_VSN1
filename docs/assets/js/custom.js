// Remove footer credits and fix button styling after page loads
document.addEventListener('DOMContentLoaded', function() {
  // Remove any element containing "mattgraham", "Theme by", or "Hosted on GitHub Pages"
  const removeTextContent = ['mattgraham', 'Theme by', 'Hosted on GitHub Pages'];
  
  removeTextContent.forEach(text => {
    const elements = document.querySelectorAll('*');
    elements.forEach(el => {
      if (el.textContent.includes(text) && el.children.length === 0) {
        // Remove the text node or the entire element if it's small
        if (el.parentElement) {
          el.parentElement.removeChild(el);
        }
      }
    });
  });
  
  // Also remove common footer wrapper elements
  const footerSelectors = ['#footer_wrap', '.footer_wrap', 'footer', '.credits'];
  footerSelectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => el.remove());
  });
  
  // Force style on View on GitHub button
  const buttons = document.querySelectorAll('#header nav a, .fork a, nav li a');
  buttons.forEach(btn => {
    btn.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    btn.style.color = '#ffffff';
    btn.style.textShadow = '0 1px 2px rgba(0,0,0,0.3)';
    btn.style.border = 'none';
    btn.style.fontWeight = '600';
  });
});

