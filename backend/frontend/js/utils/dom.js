/**
 * DOM Utilities
 *
 * Helper functions for DOM manipulation and query selection.
 */

/**
 * Safe querySelector wrapper
 * @param {string} selector - CSS selector
 * @param {Element} context - Context element (default: document)
 * @returns {Element|null} Found element
 */
export function $(selector, context = document) {
    return context.querySelector(selector);
}

/**
 * Safe querySelectorAll wrapper
 * @param {string} selector - CSS selector
 * @param {Element} context - Context element (default: document)
 * @returns {NodeList} Found elements
 */
export function $$(selector, context = document) {
    return context.querySelectorAll(selector);
}

/**
 * Get element by ID
 * @param {string} id - Element ID
 * @returns {Element|null} Found element
 */
export function getById(id) {
    return document.getElementById(id);
}

/**
 * Show element by removing 'hidden' class
 * @param {string|Element} element - Element or selector
 */
export function show(element) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.classList.remove('hidden');
    }
}

/**
 * Hide element by adding 'hidden' class
 * @param {string|Element} element - Element or selector
 */
export function hide(element) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.classList.add('hidden');
    }
}

/**
 * Toggle element visibility
 * @param {string|Element} element - Element or selector
 */
export function toggle(element) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.classList.toggle('hidden');
    }
}

/**
 * Add class to element
 * @param {string|Element} element - Element or selector
 * @param {string} className - Class name to add
 */
export function addClass(element, className) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.classList.add(className);
    }
}

/**
 * Remove class from element
 * @param {string|Element} element - Element or selector
 * @param {string} className - Class name to remove
 */
export function removeClass(element, className) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.classList.remove(className);
    }
}

/**
 * Check if element has class
 * @param {string|Element} element - Element or selector
 * @param {string} className - Class name to check
 * @returns {boolean} True if element has class
 */
export function hasClass(element, className) {
    const el = typeof element === 'string' ? $(element) : element;
    return el ? el.classList.contains(className) : false;
}

/**
 * Set text content of element
 * @param {string|Element} element - Element or selector
 * @param {string} text - Text content
 */
export function setText(element, text) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.textContent = text;
    }
}

/**
 * Set HTML content of element
 * @param {string|Element} element - Element or selector
 * @param {string} html - HTML content
 */
export function setHTML(element, html) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.innerHTML = html;
    }
}

/**
 * Create element with attributes and content
 * @param {string} tag - Element tag name
 * @param {object} attributes - Element attributes
 * @param {string|Element|Array} children - Child content
 * @returns {Element} Created element
 */
export function createElement(tag, attributes = {}, children = null) {
    const element = document.createElement(tag);

    // Set attributes
    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'dataset') {
            Object.entries(value).forEach(([dataKey, dataValue]) => {
                element.dataset[dataKey] = dataValue;
            });
        } else if (key.startsWith('on') && typeof value === 'function') {
            element.addEventListener(key.substring(2).toLowerCase(), value);
        } else {
            element.setAttribute(key, value);
        }
    });

    // Add children
    if (children) {
        if (typeof children === 'string') {
            element.textContent = children;
        } else if (children instanceof Element) {
            element.appendChild(children);
        } else if (Array.isArray(children)) {
            children.forEach(child => {
                if (child instanceof Element) {
                    element.appendChild(child);
                } else if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                }
            });
        }
    }

    return element;
}

/**
 * Remove element from DOM
 * @param {string|Element} element - Element or selector
 */
export function remove(element) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.remove();
    }
}

/**
 * Add event listener to element
 * @param {string|Element} element - Element or selector
 * @param {string} event - Event name
 * @param {function} handler - Event handler
 */
export function on(element, event, handler) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.addEventListener(event, handler);
    }
}

/**
 * Remove event listener from element
 * @param {string|Element} element - Element or selector
 * @param {string} event - Event name
 * @param {function} handler - Event handler
 */
export function off(element, event, handler) {
    const el = typeof element === 'string' ? $(element) : element;
    if (el) {
        el.removeEventListener(event, handler);
    }
}

/**
 * Get form data as object
 * @param {string|HTMLFormElement} form - Form element or selector
 * @returns {object} Form data object
 */
export function getFormData(form) {
    const formEl = typeof form === 'string' ? $(form) : form;
    if (!formEl) return {};

    const formData = new FormData(formEl);
    const data = {};

    for (const [key, value] of formData.entries()) {
        data[key] = value;
    }

    return data;
}

/**
 * Reinitialize Lucide icons
 * Should be called after dynamically adding new icons to the DOM
 */
export function initLucideIcons() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}
