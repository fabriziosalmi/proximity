"""Debug script to check modal visibility"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('http://127.0.0.1:8765')
    page.evaluate('window.localStorage.clear(); window.sessionStorage.clear();')
    page.reload()
    page.wait_for_load_state('networkidle')
    
    # Check initial state
    result = page.evaluate('''() => {
        const modal = document.getElementById('authModal');
        const isAuth = typeof Auth !== 'undefined' ? Auth.isAuthenticated() : 'Auth undefined';
        const hasShowFunc = typeof showAuthModal === 'function';
        
        return {
            isAuth: isAuth,
            hasShowFunc: hasShowFunc,
            modalClasses: modal ? modal.className : 'no modal',
            modalDisplay: modal ? modal.style.display : 'no modal',
            modalOffsetParent: modal ? (modal.offsetParent !== null) : false
        };
    }''')
    
    print('Initial state:', result)
    
    # Try to show modal
    page.evaluate('''() => {
        const modal = document.getElementById('authModal');
        if (typeof showAuthModal === 'function') {
            showAuthModal();
        }
        modal.style.display = 'block';
        modal.classList.add('show');
    }''')
    
    time.sleep(1)
    
    # Check after showing
    result2 = page.evaluate('''() => {
        const modal = document.getElementById('authModal');
        return {
            modalClasses: modal.className,
            modalDisplay: modal.style.display,
            computedDisplay: window.getComputedStyle(modal).display,
            modalOffsetParent: modal.offsetParent !== null,
            isVisible: modal.checkVisibility ? modal.checkVisibility() : 'no checkVisibility'
        };
    }''')
    
    print('After showing:', result2)
    
    input('Press Enter to close...')
    browser.close()
