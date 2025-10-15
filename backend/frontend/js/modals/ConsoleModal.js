/**
 * Console Modal Module
 *
 * Handles interactive terminal console for apps:
 * - XTerm.js terminal integration
 * - Command execution via API
 * - Command history (up/down arrows)
 * - Terminal input handling (backspace, Ctrl+C, Ctrl+L)
 * - Real-time command execution
 * - Proper cleanup on modal close
 */

import * as API from '../services/api.js';
import * as Auth from '../utils/auth.js';
import { showNotification } from '../utils/notifications.js';

// Terminal state
let terminalInstance = null;
let terminalFitAddon = null;
let currentAppId = null;
let currentHostname = null;
let commandHistory = [];
let historyIndex = -1;
let currentCommand = '';

/**
 * Show console modal for an app
 * @param {string} appId - App ID
 * @param {string} hostname - App hostname
 */
export function showAppConsole(appId, hostname) {
    // Check authentication first
    if (!Auth.isAuthenticated()) {
        console.warn('⚠️  User not authenticated - showing login modal');
        showNotification('Please login to access the console', 'warning');

        // Import auth modal dynamically to avoid circular dependency
        import('../components/auth-ui.js').then(module => {
            module.showAuthModal();
        });
        return;
    }

    const modal = document.getElementById('deployModal');
    const modalBody = document.getElementById('modalBody');

    // Hide the modal header for console view
    const modalHeader = modal.querySelector('.modal-header');
    if (modalHeader) {
        modalHeader.style.display = 'none';
    }

    // Remove all padding for console view
    modalBody.style.padding = '0';

    modalBody.innerHTML = `
        <div id="xtermContainer" style="position: relative; background: #000; border: 2px solid var(--border-cyan); border-radius: 15px; height: 92vh; padding: 0.5rem;">
            <button onclick="window.closeConsoleModal()"
                onmouseover="this.style.background='rgba(239, 68, 68, 0.2)'; this.style.borderColor='#ef4444'; this.style.color='#ef4444';"
                onmouseout="this.style.background='rgba(0, 0, 0, 0.5)'; this.style.borderColor='var(--border-cyan)'; this.style.color='var(--text-secondary)';"
                style="position: absolute; top: 0.75rem; right: 0.75rem; width: 36px; height: 36px; border-radius: var(--radius-md); background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(10px); border: 1px solid var(--border-cyan); color: var(--text-secondary); cursor: pointer; transition: var(--transition); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; z-index: 1000; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);">✕</button>
        </div>
    `;

    modal.classList.add('show');
    openModal(); // Prevent body scrolling

    // Initialize xterm.js
    setTimeout(() => initializeXterm(appId, hostname), 100);
}

/**
 * Initialize XTerm.js terminal
 * @param {string} appId - App ID
 * @param {string} hostname - App hostname
 */
function initializeXterm(appId, hostname) {
    currentAppId = appId;
    currentHostname = hostname;

    // Clean up existing terminal if any
    if (terminalInstance) {
        terminalInstance.dispose();
        terminalInstance = null;
    }

    const container = document.getElementById('xtermContainer');
    if (!container) return;

    // Create terminal with custom theme
    terminalInstance = new Terminal({
        cursorBlink: true,
        cursorStyle: 'block',
        fontSize: 14,
        fontFamily: '"Cascadia Code", "Courier New", monospace',
        theme: {
            background: '#000000',
            foreground: '#e0e0e0',
            cursor: '#4ade80',
            black: '#000000',
            red: '#ef4444',
            green: '#4ade80',
            yellow: '#fbbf24',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#e0e0e0',
            brightBlack: '#666666',
            brightRed: '#f87171',
            brightGreen: '#86efac',
            brightYellow: '#fcd34d',
            brightBlue: '#60a5fa',
            brightMagenta: '#c084fc',
            brightCyan: '#22d3ee',
            brightWhite: '#ffffff'
        },
        rows: 24,
        cols: 80
    });

    // Add fit addon
    terminalFitAddon = new FitAddon.FitAddon();
    terminalInstance.loadAddon(terminalFitAddon);

    // Open terminal in container
    terminalInstance.open(container);
    terminalFitAddon.fit();

    // Write welcome message
    terminalInstance.writeln('\x1b[1;32mProximity Console\x1b[0m');
    terminalInstance.writeln(`Connected to: \x1b[1;36m${hostname}\x1b[0m`);
    terminalInstance.writeln('Type commands and press Enter to execute.');
    terminalInstance.writeln('');
    writePrompt();

    // Handle terminal input
    terminalInstance.onData(data => handleTerminalInput(data));

    // Handle window resize
    const resizeObserver = new ResizeObserver(() => {
        if (terminalFitAddon && terminalInstance) {
            try {
                terminalFitAddon.fit();
            } catch (e) {
                // Ignore resize errors
            }
        }
    });
    resizeObserver.observe(container);

    // Store observer for cleanup
    container._resizeObserver = resizeObserver;

    // Focus terminal
    terminalInstance.focus();
}

/**
 * Write command prompt
 */
function writePrompt() {
    if (!terminalInstance) return;
    terminalInstance.write(`\x1b[1;32mproximity@${currentHostname}\x1b[0m:\x1b[1;34m~\x1b[0m$ `);
}

/**
 * Handle terminal input (keyboard events)
 * @param {string} data - Input data
 */
function handleTerminalInput(data) {
    if (!terminalInstance) return;

    const code = data.charCodeAt(0);

    // Handle Enter key
    if (code === 13) {
        terminalInstance.write('\r\n');
        if (currentCommand.trim()) {
            commandHistory.push(currentCommand);
            historyIndex = commandHistory.length;
            executeTerminalCommand(currentCommand.trim());
        } else {
            writePrompt();
        }
        currentCommand = '';
        return;
    }

    // Handle Backspace
    if (code === 127) {
        if (currentCommand.length > 0) {
            currentCommand = currentCommand.slice(0, -1);
            terminalInstance.write('\b \b');
        }
        return;
    }

    // Handle Ctrl+C
    if (code === 3) {
        terminalInstance.write('^C\r\n');
        currentCommand = '';
        writePrompt();
        return;
    }

    // Handle Ctrl+L (clear)
    if (code === 12) {
        terminalInstance.clear();
        currentCommand = '';
        writePrompt();
        return;
    }

    // Handle Up Arrow (previous command)
    if (data === '\x1b[A') {
        if (historyIndex > 0) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();

            historyIndex--;
            currentCommand = commandHistory[historyIndex];
            terminalInstance.write(currentCommand);
        }
        return;
    }

    // Handle Down Arrow (next command)
    if (data === '\x1b[B') {
        if (historyIndex < commandHistory.length - 1) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();

            historyIndex++;
            currentCommand = commandHistory[historyIndex];
            terminalInstance.write(currentCommand);
        } else if (historyIndex === commandHistory.length - 1) {
            // Clear current line
            terminalInstance.write('\r\x1b[K');
            writePrompt();

            historyIndex = commandHistory.length;
            currentCommand = '';
        }
        return;
    }

    // Ignore other control sequences
    if (code === 27 || data.startsWith('\x1b')) {
        return;
    }

    // Add character to command
    currentCommand += data;
    terminalInstance.write(data);
}

/**
 * Execute terminal command via API
 * @param {string} command - Command to execute
 */
async function executeTerminalCommand(command) {
    if (!terminalInstance || !currentAppId) return;

    // Double-check authentication before executing
    if (!Auth.isAuthenticated()) {
        console.error('[Terminal] Not authenticated - no token found');
        terminalInstance.writeln('\r\n\x1b[1;31mError: Not authenticated. Please login first.\x1b[0m\r\n');

        import('../components/auth-ui.js').then(module => {
            module.showAuthModal();
        });
        return;
    }

    console.log('[Terminal] Executing command:', command, 'for app:', currentAppId);
    console.log('[Terminal] Token exists:', !!Auth.getToken());

    try {
        const response = await API.execCommand(currentAppId, command);

        console.log('[Terminal] Response data:', response);

        if (response.success && response.output) {
            // Write output line by line
            const lines = response.output.split('\n');
            lines.forEach(line => {
                terminalInstance.writeln(line);
            });
        } else if (response.error) {
            terminalInstance.writeln(`\x1b[1;31m${response.error}\x1b[0m`);
        }
    } catch (error) {
        console.error('[Terminal] Execution error:', error);
        terminalInstance.writeln(`\x1b[1;31mError: ${error.message}\x1b[0m`);
    }

    writePrompt();
}

/**
 * Cleanup terminal resources
 */
export function cleanupTerminal() {
    if (terminalInstance) {
        terminalInstance.dispose();
        terminalInstance = null;
        terminalFitAddon = null;
    }

    const container = document.getElementById('xtermContainer');
    if (container && container._resizeObserver) {
        container._resizeObserver.disconnect();
        delete container._resizeObserver;
    }

    currentAppId = null;
    currentHostname = null;
    currentCommand = '';
}

/**
 * Close console modal
 */
export function closeConsoleModal() {
    cleanupTerminal();

    const modal = document.getElementById('deployModal');
    const modalBody = modal.querySelector('.modal-body');

    // Restore modal header visibility
    const modalHeader = modal.querySelector('.modal-header');
    if (modalHeader) {
        modalHeader.style.display = '';
    }

    // Restore modal body padding
    if (modalBody) {
        modalBody.style.padding = '';
    }

    modal.classList.remove('show');
    closeModal();
    
    // CRITICAL FIX: Force restore pointer events even if closeModal didn't work
    setTimeout(() => {
        const mainContent = document.querySelector('.app-container');
        if (mainContent && mainContent.style.pointerEvents === 'none') {
            console.warn('⚠️ Force restoring pointer events after console close');
            mainContent.style.pointerEvents = '';
        }
        
        // Also ensure modal-open is removed from body if no modals are open
        const anyModalOpen = document.querySelector('.modal.show');
        if (!anyModalOpen && document.body.classList.contains('modal-open')) {
            console.warn('⚠️ Force removing modal-open class after console close');
            document.body.classList.remove('modal-open');
            document.body.style.top = '';
        }
    }, 100);
}

/**
 * Open modal (prevent body scrolling)
 */
function openModal() {
    const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    document.body.classList.add('modal-open');
    document.body.style.top = `-${scrollPosition}px`;

    const mainContent = document.querySelector('.app-container');
    if (mainContent) {
        mainContent.style.pointerEvents = 'none';
    }
}

/**
 * Close modal (restore body scrolling)
 */
function closeModal() {
    const anyModalOpen = Array.from(document.querySelectorAll('.modal.show')).length > 0;
    if (!anyModalOpen) {
        const scrollPosition = parseInt(document.body.style.top || '0') * -1;
        document.body.classList.remove('modal-open');
        document.body.style.top = '';

        const mainContent = document.querySelector('.app-container');
        if (mainContent) {
            mainContent.style.pointerEvents = '';
        }

        window.scrollTo(0, scrollPosition);
    }
}

// Expose functions globally for legacy compatibility
if (typeof window !== 'undefined') {
    window.showAppConsole = showAppConsole;
    window.cleanupTerminal = cleanupTerminal;
    window.closeConsoleModal = closeConsoleModal;
    
    // Override global closeModal when console is active
    const originalCloseModal = window.closeModal;
    window.closeModal = function() {
        // If terminal is active, use proper cleanup
        if (terminalInstance) {
            closeConsoleModal();
        } else if (originalCloseModal) {
            originalCloseModal();
        }
    };
}
