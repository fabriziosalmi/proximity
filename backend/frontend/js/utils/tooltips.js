/**
 * Custom Tooltip System for Proximity
 *
 * A lightweight, beautiful tooltip solution that replaces native browser tooltips
 * with custom-styled tooltips matching the Proximity design language.
 *
 * @module tooltips
 */

let activeTooltip = null;
let tooltipTimeout = null;

/**
 * Initialize tooltip system
 * Attaches event listeners to all elements with [data-tooltip] attribute
 * @param {HTMLElement} container - Optional container to scope tooltip initialization (MUCH faster!)
 */
export function initTooltips(container = null) {
    console.time('⏱️ Init Tooltips');

    // PERFORMANCE: Only query elements within the specified container
    // This is MUCH faster than scanning the entire document
    const tooltipElements = container
        ? container.querySelectorAll('[data-tooltip]')
        : document.querySelectorAll('[data-tooltip]');

    tooltipElements.forEach(element => {
        // Remove any existing listeners to prevent duplicates
        element.removeEventListener('mouseenter', handleTooltipShow);
        element.removeEventListener('mouseleave', handleTooltipHide);

        // Add new listeners
        element.addEventListener('mouseenter', handleTooltipShow);
        element.addEventListener('mouseleave', handleTooltipHide);
    });

    console.log(`✓ Tooltip system initialized for ${tooltipElements.length} elements${container ? ` in ${container.id || 'container'}` : ' (document-wide)'}`);
    console.timeEnd('⏱️ Init Tooltips');
}

/**
 * Show tooltip on mouseenter
 * @param {MouseEvent} event - The mouseenter event
 */
function handleTooltipShow(event) {
    const element = event.currentTarget;
    const tooltipText = element.getAttribute('data-tooltip');

    // Don't show tooltip if text is empty or element is disabled
    if (!tooltipText || element.disabled || element.classList.contains('disabled')) {
        return;
    }

    // Clear any existing timeout
    if (tooltipTimeout) {
        clearTimeout(tooltipTimeout);
    }

    // Small delay before showing tooltip for better UX
    tooltipTimeout = setTimeout(() => {
        showTooltip(element, tooltipText);
    }, 300);
}

/**
 * Hide tooltip on mouseleave
 */
function handleTooltipHide() {
    // Clear timeout if user moves away before tooltip shows
    if (tooltipTimeout) {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = null;
    }

    hideTooltip();
}

/**
 * Create and show tooltip element
 * @param {HTMLElement} targetElement - The element to attach tooltip to
 * @param {string} text - Tooltip text content
 */
function showTooltip(targetElement, text) {
    // Remove any existing tooltip
    hideTooltip();

    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'proximity-tooltip';
    tooltip.textContent = text;
    tooltip.setAttribute('role', 'tooltip');

    // Add to DOM
    document.body.appendChild(tooltip);

    // Calculate position
    const targetRect = targetElement.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    // Determine if tooltip should be above or below
    const spaceBelow = window.innerHeight - targetRect.bottom;
    const spaceAbove = targetRect.top;
    const tooltipHeight = tooltipRect.height;

    let top, left;
    let position = 'bottom'; // default

    // Check if there's enough space below
    if (spaceBelow >= tooltipHeight + 12) {
        // Show below
        top = targetRect.bottom + 8;
        position = 'bottom';
    } else if (spaceAbove >= tooltipHeight + 12) {
        // Show above
        top = targetRect.top - tooltipHeight - 8;
        position = 'top';
        tooltip.classList.add('top');
    } else {
        // Default to below even if cramped
        top = targetRect.bottom + 8;
        position = 'bottom';
    }

    // Center horizontally
    left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);

    // Ensure tooltip doesn't go off-screen horizontally
    const padding = 8;
    if (left < padding) {
        left = padding;
    } else if (left + tooltipRect.width > window.innerWidth - padding) {
        left = window.innerWidth - tooltipRect.width - padding;
    }

    // Apply position
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;

    // Show tooltip with animation
    requestAnimationFrame(() => {
        tooltip.classList.add('show');
    });

    // Store reference to active tooltip
    activeTooltip = tooltip;
}

/**
 * Hide and remove tooltip element
 */
function hideTooltip() {
    if (activeTooltip) {
        activeTooltip.classList.remove('show');

        // Remove from DOM after transition
        setTimeout(() => {
            if (activeTooltip && activeTooltip.parentNode) {
                activeTooltip.parentNode.removeChild(activeTooltip);
            }
            activeTooltip = null;
        }, 200);
    }
}

/**
 * Refresh tooltips (useful when DOM is updated)
 * Call this after adding new elements with data-tooltip attributes
 * @param {HTMLElement} container - Optional container to scope refresh (MUCH faster!)
 */
export function refreshTooltips(container = null) {
    // Hide any active tooltip
    hideTooltip();

    // Re-initialize with optional container scope
    initTooltips(container);
}

// Export for global access if needed
if (typeof window !== 'undefined') {
    window.initTooltips = initTooltips;
    window.refreshTooltips = refreshTooltips;
}
