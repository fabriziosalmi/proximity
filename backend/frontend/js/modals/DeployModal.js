/**
 * Deploy Modal Module
 *
 * Handles application deployment:
 * - Deployment configuration form
 * - Real-time deployment progress tracking
 * - Progress visualization with step indicators
 * - Deployment status polling
 */

import * as API from '../services/api.js';
import * as AppState from '../state/appState.js';
import { showNotification } from '../utils/notifications.js';
import { SoundService } from '../services/soundService.js';

const API_BASE = 'http://localhost:8765/api/v1';

// Deployment progress tracking
let deploymentProgressInterval = null;

/**
 * Show deployment modal for a catalog app
 * @param {string} catalogId - Catalog app ID
 */
export function showDeployModal(catalogId) {
    console.log(`📋 showDeployModal called with catalogId: ${catalogId}`);
    
    const state = AppState.getState();
    console.log(`   State has catalog:`, !!state.catalog);
    console.log(`   Catalog has items:`, state.catalog?.items?.length || 0);
    
    const app = state.catalog?.items?.find(a => a.id === catalogId);

    if (!app) {
        console.error('❌ Catalog app not found:', catalogId);
        console.error('   Available app IDs:', state.catalog?.items?.map(a => a.id).slice(0, 5));
        console.error('   ⚠️ EARLY RETURN - no app found');
        return;
    }

    console.log(`✅ Found app: ${app.name}`);
    const modal = document.getElementById('deployModal');
    console.log(`   Modal element found:`, !!modal);
    console.log(`   Modal classes before:`, modal?.className);
    document.getElementById('modalTitle').textContent = `Deploy ${app.name}`;

    document.getElementById('modalBody').innerHTML = `
        <div class="alert info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-content">
                <div class="alert-message">${app.description}</div>
            </div>
        </div>

        <form id="deployForm">
            <div class="form-group">
                <label class="form-label">Hostname <span class="required">*</span></label>
                <input type="text" class="form-input" id="hostname" value="${app.id}-01" required>
                <p class="form-help">Unique identifier for this application instance</p>
            </div>

            <div class="form-group">
                <label class="form-label">Target Node</label>
                <select class="form-input" id="targetNode">
                    <option value="">Auto-select (recommended)</option>
                    ${state.nodes.map(node => `
                        <option value="${node.node}">${node.node} (${Math.round((node.mem / node.maxmem) * 100)}% used)</option>
                    `).join('')}
                </select>
                <p class="form-help">Leave empty to automatically select the best node</p>
            </div>

            <div class="app-meta">
                <div class="app-meta-item">
                    <span>💾</span>
                    <span>${app.min_memory}MB RAM required</span>
                </div>
                <div class="app-meta-item">
                    <span>⚡</span>
                    <span>${app.min_cpu} vCPU required</span>
                </div>
            </div>
        </form>
    `;

    const footer = `
        <button class="btn btn-secondary" id="deployCancelBtn">Cancel</button>
        <button class="btn btn-primary" id="deploySubmitBtn">
            Deploy Application
        </button>
    `;

    document.querySelector('.modal-footer')?.remove();
    const footerDiv = document.createElement('div');
    footerDiv.className = 'modal-footer';
    footerDiv.innerHTML = footer;
    document.querySelector('.modal-content').appendChild(footerDiv);

    // Attach event listeners
    document.getElementById('deployCancelBtn').addEventListener('click', closeDeployModal);
    document.getElementById('deploySubmitBtn').addEventListener('click', () => deployApp(catalogId));
    document.getElementById('deployForm').addEventListener('submit', (e) => {
        e.preventDefault();
        deployApp(catalogId);
    });

    console.log(`   Adding 'show' class to modal...`);
    modal.classList.add('show');
    console.log(`   Modal classes after:`, modal.className);
    console.log(`   Calling openModal()...`);
    openModal();
    console.log(`   ✅ showDeployModal complete`);
}

/**
 * Deploy application
 * @param {string} catalogId - Catalog app ID
 */
async function deployApp(catalogId) {
    const hostname = document.getElementById('hostname')?.value;
    const targetNode = document.getElementById('targetNode')?.value || null;

    if (!hostname) {
        showNotification('Please enter a hostname', 'error');
        return;
    }

    closeDeployModal();

    // Play deploy start sound
    SoundService.play('deploy_start');

    // Start ambient deployment loop after a short delay
    setTimeout(() => {
        SoundService.startLoop('deployment_loop', 2.0);
    }, 500);

    try {
        const payload = {
            catalog_id: catalogId,
            hostname: hostname,
            config: {},
            environment: {}
        };

        if (targetNode) {
            payload.node = targetNode;
        }

        // Add breadcrumb for deployment start
        if (window.addDebugBreadcrumb) {
            window.addDebugBreadcrumb('App deployment started', {
                catalog_id: catalogId,
                hostname: hostname,
                target_node: targetNode || 'auto'
            });
        }

        // Show deployment progress modal
        showDeploymentProgress(catalogId, hostname);

        const result = await API.deployApp(payload);

        // Stop deployment loop with fade out, then play explosion
        await SoundService.stopLoop(2.0);
        SoundService.play('explosion');

        hideDeploymentProgress();
        closeDeployModal();
        showNotification(`Application deployed successfully!`, 'success');

        // Add breadcrumb for successful deployment
        if (window.addDebugBreadcrumb) {
            window.addDebugBreadcrumb('App deployment succeeded', {
                catalog_id: catalogId,
                hostname: hostname,
                lxc_id: result.lxc_id
            });
        }

        // Wait for proxy vhost to be fully propagated
        console.log('Waiting for proxy vhost propagation...');
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Reload apps and update state
        const apps = await API.getApps();
        const systemInfo = await API.getSystemInfo();

        AppState.setState({
            apps: apps,
            deployedApps: apps,
            systemInfo: systemInfo,
            currentView: 'apps'
        });

    } catch (error) {
        // Stop deployment loop immediately on error
        await SoundService.stopLoop(1.0);

        hideDeploymentProgress();
        closeDeployModal();
        showNotification('Deployment failed: ' + error.message, 'error');
        console.error('Deployment error:', error);

        // Report deployment failure to Sentry
        if (window.reportToSentry) {
            window.reportToSentry(error, {
                context: 'app_deployment',
                catalog_id: catalogId,
                hostname: hostname,
                target_node: targetNode || 'auto',
                error_message: error.message
            });
        }

        // Add breadcrumb for failed deployment
        if (window.addDebugBreadcrumb) {
            window.addDebugBreadcrumb('App deployment failed', {
                catalog_id: catalogId,
                hostname: hostname,
                error: error.message
            });
        }
    }
}

/**
 * Show deployment progress modal
 * @param {string} catalogId - Catalog app ID
 * @param {string} hostname - App hostname
 */
function showDeploymentProgress(catalogId, hostname) {
    const modal = document.getElementById('deployModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');

    modalTitle.textContent = 'Deploying Application';

    modalBody.innerHTML = `
        <div style="text-align: center; padding: 2rem 1rem;">
            <div style="margin-bottom: 1.5rem;">
                <div class="loading-spinner" style="display: inline-block; margin-bottom: 1rem;"></div>
                <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">${hostname}</h3>
                <p style="color: var(--text-secondary); font-size: 0.875rem;">Setting up your application</p>
            </div>

            <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 1.5rem; margin-bottom: 1rem;">
                <div id="progressSteps" style="text-align: left;">
                    <div class="progress-step active">
                        <div class="progress-step-icon">🟠</div>
                        <div class="progress-step-text">Creating LXC container</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Starting container</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Installing Docker</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Pulling Docker images</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Starting services</div>
                    </div>
                    <div class="progress-step">
                        <div class="progress-step-icon">⚪</div>
                        <div class="progress-step-text">Finalizing deployment</div>
                    </div>
                </div>
            </div>

            <div style="width: 100%; background: var(--bg-tertiary); border-radius: var(--radius-md); height: 8px; overflow: hidden; margin-bottom: 1rem;">
                <div id="progressBar" style="width: 10%; height: 100%; background: linear-gradient(90deg, var(--primary), var(--secondary)); transition: width 0.5s ease;"></div>
            </div>

            <div id="progressMessage" style="color: var(--text-tertiary); font-size: 0.875rem; min-height: 1.5rem;">
                Initializing deployment...
            </div>

            <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border);">
                <p style="color: var(--text-tertiary); font-size: 0.75rem; margin-bottom: 0.5rem;">
                    This may take 2-5 minutes
                </p>
                <p style="color: var(--text-tertiary); font-size: 0.75rem;">
                    Docker images are being downloaded and configured
                </p>
            </div>
        </div>
    `;

    // Remove footer since deployment is already in progress
    document.querySelector('.modal-footer')?.remove();

    modal.classList.add('show');
    modal.style.pointerEvents = 'none'; // Prevent closing during deployment
    openModal();

    // Start polling for real deployment status
    pollDeploymentStatus(`${catalogId}-${hostname}`);
}

/**
 * Poll deployment status and update progress
 * @param {string} appId - App ID
 */
async function pollDeploymentStatus(appId) {
    let pollAttempts = 0;
    const maxAttempts = 120; // 120 attempts * 2 seconds = 4 minutes max
    let lastKnownProgress = 10; // Start at 10%

    deploymentProgressInterval = setInterval(async () => {
        pollAttempts++;

        try {
            const status = await API.getDeploymentStatus(appId);
            console.log('✓ Deployment status received:', status);

            // Update UI with real status
            updateDeploymentProgress(status);
            lastKnownProgress = status.progress || lastKnownProgress;

            // Check if deployment is complete or failed
            if (status.status === 'running' || status.status === 'error') {
                clearInterval(deploymentProgressInterval);
                deploymentProgressInterval = null;
                console.log('✓ Deployment complete or failed, stopping polling');
            }
        } catch (error) {
            console.error('Error polling deployment status:', error);

            // Use simulated progress if real status not available
            if (lastKnownProgress < 90) {
                lastKnownProgress += Math.random() * 2 + 1;

                const simulatedStep = getStepFromProgress(lastKnownProgress);
                updateDeploymentProgress({
                    progress: Math.min(lastKnownProgress, 90),
                    current_step: simulatedStep,
                    message: simulatedStep
                });
            }
        }

        // Stop polling after max attempts
        if (pollAttempts >= maxAttempts) {
            clearInterval(deploymentProgressInterval);
            deploymentProgressInterval = null;
            console.warn('⚠️ Deployment polling timeout reached');
        }
    }, 2000); // Poll every 2 seconds
}

/**
 * Get deployment step from progress percentage
 * @param {number} progress - Progress percentage (0-100)
 * @returns {string} Step name
 */
function getStepFromProgress(progress) {
    if (progress < 20) return 'Creating LXC container';
    if (progress < 35) return 'Starting container';
    if (progress < 50) return 'Installing Docker';
    if (progress < 70) return 'Pulling Docker images';
    if (progress < 85) return 'Starting services';
    return 'Finalizing deployment';
}

/**
 * Update deployment progress UI
 * @param {object} status - Deployment status object
 */
function updateDeploymentProgress(status) {
    const progressBar = document.getElementById('progressBar');
    const progressMessage = document.getElementById('progressMessage');

    if (progressBar) {
        const progress = status.progress || 0;
        progressBar.style.width = `${progress}%`;
    }

    if (progressMessage) {
        const message = status.current_step || status.message || 'Processing...';
        progressMessage.textContent = message;
    }

    // Update step indicators
    const progressSteps = document.getElementById('progressSteps');
    if (progressSteps && (status.current_step || status.message)) {
        updateProgressSteps(status.current_step || status.message);
    }
}

/**
 * Update progress step indicators
 * @param {string} currentStepText - Current step description
 */
function updateProgressSteps(currentStepText) {
    const progressSteps = document.getElementById('progressSteps');
    if (!progressSteps) return;

    // Map status text to step names
    const stepMap = {
        'Creating container': 'creating',
        'Reserving container ID': 'creating',
        'Creating LXC': 'creating',
        'Starting container': 'starting',
        'Container started': 'starting',
        'Setting up Docker': 'docker',
        'Installing Docker': 'docker',
        'Docker installed': 'docker',
        'Pulling Docker images': 'images',
        'Pulling images': 'images',
        'Images pulled': 'images',
        'Setting up application': 'services',
        'Starting application': 'services',
        'Configuring reverse proxy': 'services',
        'Application started': 'services',
        'Finalizing deployment': 'finalizing',
        'Deployment complete': 'finalizing',
        'Complete': 'finalizing'
    };

    // Find which step we're on
    let currentStep = 'creating';
    for (const [text, step] of Object.entries(stepMap)) {
        if (currentStepText.toLowerCase().includes(text.toLowerCase())) {
            currentStep = step;
            break;
        }
    }

    const allSteps = ['creating', 'starting', 'docker', 'images', 'services', 'finalizing'];
    const stepMessages = {
        creating: 'Creating LXC container',
        starting: 'Starting container',
        docker: 'Installing Docker',
        images: 'Pulling Docker images',
        services: 'Starting services',
        finalizing: 'Finalizing deployment'
    };

    const currentStepIndex = allSteps.indexOf(currentStep);

    // Update the steps display with colored circles
    progressSteps.innerHTML = allSteps.map((step, index) => {
        const isDone = index < currentStepIndex;
        const isCurrent = step === currentStep;
        const icon = isDone ? '🟢' : (isCurrent ? '🟠' : '⚪');
        const stepClass = isDone ? 'completed' : (isCurrent ? 'active' : '');

        return `
            <div class="progress-step ${stepClass}">
                <div class="progress-step-icon">${icon}</div>
                <div class="progress-step-text">${stepMessages[step]}</div>
            </div>
        `;
    }).join('');
}

/**
 * Hide deployment progress modal
 */
function hideDeploymentProgress() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('show');
    modal.style.pointerEvents = 'auto';

    if (deploymentProgressInterval) {
        clearInterval(deploymentProgressInterval);
        deploymentProgressInterval = null;
    }

    closeModal();
}

/**
 * Close deploy modal
 */
function closeDeployModal() {
    const modal = document.getElementById('deployModal');
    modal.classList.remove('show');
    closeModal();
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
    window.showDeployModal = showDeployModal;
    window.closeModal = closeDeployModal;
}
