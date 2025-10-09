/**
 * Proximity - First Run Onboarding Module
 * 
 * This module handles the "Power On" experience for first-time users.
 * It is completely isolated from the main application logic and authentication flows.
 * 
 * Core Functionality:
 * - Checks if this is the first run via API
 * - If first run: displays Power On screen and waits for user interaction
 * - If not first run: immediately returns control to main app
 * - Uses Promise-based flow to ensure proper sequencing
 * 
 * @module onboarding
 */

/**
 * Handle the onboarding flow for first-time users.
 * 
 * This function returns a Promise that:
 * - Resolves immediately if not first run
 * - Resolves after user interaction if first run
 * 
 * The main application should await this function before proceeding with
 * normal initialization (auth checks, dashboard loading, etc.)
 * 
 * @returns {Promise<boolean>} Resolves to true when onboarding is complete
 * 
 * @example
 * async function initializeApp() {
 *   await handleOnboarding(); // Waits here if first run
 *   // Continue with normal app initialization...
 * }
 */
export async function handleOnboarding() {
    return new Promise(async (resolve) => {
        try {
            // Check if this is the first run
            const response = await fetch('/api/v1/system/status/initial');
            
            if (!response.ok) {
                console.error('Failed to check first run status:', response.status);
                resolve(true); // Proceed anyway on error
                return;
            }
            
            const data = await response.json();
            
            // Not the first run - proceed immediately
            if (!data.is_first_run) {
                console.log('✅ Not first run - skipping onboarding');
                resolve(true);
                return;
            }
            
            // This IS the first run - show the Power On experience
            console.log('🚀 First run detected - showing Power On screen');
            
            const powerOnScreen = document.getElementById('power-on-screen');
            const powerButton = document.getElementById('power-button');
            
            if (!powerOnScreen || !powerButton) {
                console.error('Power On screen elements not found');
                resolve(true);
                return;
            }
            
            // Show the Power On screen
            powerOnScreen.style.display = 'flex';
            
            // Handle power button click
            const handlePowerClick = async () => {
                console.log('⚡ Power button activated');
                
                // Add activating animation class
                powerButton.classList.add('activating');
                
                // Play power on sound if available
                if (window.SoundService && window.SoundService.play) {
                    try {
                        await window.SoundService.play('deploy_start');
                    } catch (err) {
                        console.warn('Could not play power on sound:', err);
                    }
                }
                
                // Wait for animation to complete
                await new Promise(animResolve => setTimeout(animResolve, 800));
                
                // Start boot sequence
                powerOnScreen.classList.add('booting');
                
                // Wait for fade out
                await new Promise(fadeResolve => setTimeout(fadeResolve, 800));
                
                // Hide the screen
                powerOnScreen.style.display = 'none';
                
                console.log('✅ Power On sequence complete - handing control to main app');
                
                // Resolve the promise - onboarding is complete
                resolve(true);
            };
            
            // Attach click listener (once only)
            powerButton.addEventListener('click', handlePowerClick, { once: true });
            
            // Also support keyboard interaction for accessibility
            powerButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handlePowerClick();
                }
            }, { once: true });
            
        } catch (error) {
            console.error('Onboarding error:', error);
            // On error, proceed anyway
            resolve(true);
        }
    });
}

/**
 * Export the module for ES6 imports
 */
export default { handleOnboarding };
