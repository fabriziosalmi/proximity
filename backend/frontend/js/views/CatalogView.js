/**
 * Catalog View Component
 *
 * Displays the application catalog/store.
 * THIS IS THE TRUE MIGRATION: Code moved from app.js, not recreated.
 *
 * @module views/CatalogView
 */

import { Component } from '../core/Component.js';

export class CatalogView extends Component {
    constructor() {
        super();
    }

    /**
     * Mount the catalog view
     * @param {HTMLElement} container - View container
     * @param {Object} state - Application state
     * @returns {Function} Unmount function
     */
    mount(container, state) {
        console.log('✅ Mounting Catalog View');

        // MOVED FROM app.js: renderCatalogView() function
        this.renderCatalogView(container);

        // Track click events using event delegation
        this.trackListener(container, 'click', (e) => this.handleCatalogClick(e));

        // Call parent mount
        return super.mount(container, state);
    }

    /**
     * MOVED FROM app.js (line 1246): renderCatalogView()
     * Render catalog view HTML structure
     */
    renderCatalogView(container) {
        console.log('🏪 renderCatalogView() called');
        container.classList.remove('has-sub-nav'); // Remove old sub-nav class

        if (!window.state.catalog || !window.state.catalog.items) {
            console.log('⚠️  Catalog data not loaded yet');
            container.innerHTML = '<div class="loading-spinner"></div>';
            return;
        }
        console.log(`✓ Rendering ${window.state.catalog.items.length} catalog items`);

        const content = `
            <div class="search-bar-container">
                <div class="search-bar">
                    <i data-lucide="search" class="search-icon"></i>
                    <input
                        type="text"
                        class="search-input"
                        id="catalogSearchInput"
                        placeholder="Search applications by name, description, or category..."
                        oninput="searchCatalog(this.value)"
                    />
                    <button class="search-clear" id="catalogClearSearch" onclick="clearCatalogSearch()" style="display: none;">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                <div class="search-results-count" id="catalogResultsCount" style="display: none;"></div>
            </div>

            <div class="apps-grid" id="catalogGrid"></div>
        `;

        container.innerHTML = content;

        // Render catalog app cards using template cloning (EXISTING PATTERN)
        const grid = document.getElementById('catalogGrid');
        for (const app of window.state.catalog.items) {
            // Use global renderAppCard function for now
            if (typeof window.renderAppCard === 'function') {
                window.renderAppCard(app, grid, false);
            }
        }

        // Initialize Lucide icons
        if (typeof window.initLucideIcons === 'function') {
            window.initLucideIcons();
        }

        // Hover sounds are handled automatically via event delegation (initCardHoverSounds)
    }

    /**
     * Handle catalog clicks (event delegation)
     * @param {Event} e - Click event
     */
    handleCatalogClick(e) {
        const deployBtn = e.target.closest('[data-action="deploy"]');
        if (!deployBtn) return;

        const catalogCard = deployBtn.closest('[data-catalog-id]');
        if (!catalogCard) return;

        const catalogId = catalogCard.getAttribute('data-catalog-id');
        const app = window.state.catalog.items.find(a => a.id === catalogId);

        if (!app) {
            console.error('Catalog app not found:', catalogId);
            return;
        }

        e.preventDefault();
        e.stopPropagation();

        // Delegate to global function (will be refactored later)
        if (typeof window.showDeployModal === 'function') {
            window.showDeployModal(app);
        }
    }

    /**
     * Unmount catalog view and cleanup
     */
    unmount() {
        console.log('🧹 Unmounting Catalog View');
        super.unmount();
    }
}

// Create singleton instance
export const catalogView = new CatalogView();
