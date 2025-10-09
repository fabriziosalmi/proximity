/**
 * SoundService - Professional UI Feedback Sound System
 * 
 * Provides high-quality audio feedback for user interactions with:
 * - Preloaded Audio objects for instant playback
 * - Mute/unmute with localStorage persistence
 * - Singleton pattern for centralized sound management
 * - Non-intrusive professional sounds matching futuristic aesthetic
 * 
 * Usage:
 *   import { SoundService } from './services/soundService.js';
 *   SoundService.init();
 *   SoundService.play('success');
 *   SoundService.toggleMute();
 */

export const SoundService = {
    // Internal state
    sounds: {},
    isMuted: false,
    isInitialized: false,
    masterVolume: 0.7, // Master volume (0.0 - 1.0)

    // Audio presets
    presets: {
        minimal: { volume: 0.3, name: 'Minimal' },
        standard: { volume: 0.7, name: 'Standard' },
        immersive: { volume: 1.0, name: 'Immersive' }
    },
    currentPreset: 'standard',

    // Available sound effects
    soundFiles: {
        success: '/assets/sounds/success.wav',       // Positive completion chime (800+1200+1600Hz, 0.35s)
        error: '/assets/sounds/error.wav',           // Low frequency denial (180+140Hz, 0.3s)
        click: '/assets/sounds/click.wav',           // Subtle digital blip (1400Hz, 0.08s)
        notification: '/assets/sounds/notification.wav', // Gentle attention sweep (600-900Hz, 0.4s)
        deploy_start: '/assets/sounds/deploy_start.wav', // Power-up activation (300-900Hz, 0.5s)
        deployment_loop: '/assets/sounds/deployment_loop.wav', // Dub-techno ambient (8s seamless loop)
        explosion: '/assets/sounds/explosion.wav'    // Deployment completion impact (1.2s)
    },
    
    // Loop state management
    currentLoop: null,
    fadeInterval: null,
    
    /**
     * Initialize the sound system
     * Preloads all audio files and restores mute state from localStorage
     * Call this once at application startup
     */
    init() {
        if (this.isInitialized) {
            console.warn('SoundService already initialized');
            return;
        }

        console.log('🔊 SoundService: Initializing...');

        // Restore settings from localStorage
        const savedMuteState = localStorage.getItem('proximity_sound_muted');
        this.isMuted = savedMuteState === 'true';

        const savedVolume = localStorage.getItem('proximity_sound_volume');
        if (savedVolume) {
            this.masterVolume = parseFloat(savedVolume);
        }

        const savedPreset = localStorage.getItem('proximity_sound_preset');
        if (savedPreset && this.presets[savedPreset]) {
            this.currentPreset = savedPreset;
            this.masterVolume = this.presets[savedPreset].volume;
        }

        // Preload all sound files
        for (const [name, path] of Object.entries(this.soundFiles)) {
            try {
                const audio = new Audio(path);
                audio.preload = 'auto';
                audio.volume = this.masterVolume;
                this.sounds[name] = audio;
            } catch (error) {
                console.error(`SoundService: Failed to preload ${name}:`, error);
            }
        }

        this.isInitialized = true;
        console.log(`🔊 SoundService: Initialized`);
        console.log(`   • Muted: ${this.isMuted}`);
        console.log(`   • Volume: ${Math.round(this.masterVolume * 100)}%`);
        console.log(`   • Preset: ${this.currentPreset}`);
        console.log(`   • Loaded ${Object.keys(this.sounds).length} sound effects`);
    },
    
    /**
     * Play a sound effect
     * @param {string} soundName - Name of the sound to play (success, error, click, notification, deploy_start)
     * @param {number} volume - Optional volume override (0.0 to 1.0)
     */
    play(soundName, volume = null) {
        if (!this.isInitialized) {
            console.warn('SoundService: Not initialized. Call init() first.');
            return;
        }
        
        if (this.isMuted) {
            return; // Silent when muted
        }
        
        const audio = this.sounds[soundName];
        if (!audio) {
            console.warn(`SoundService: Sound "${soundName}" not found`);
            return;
        }
        
        try {
            // Reset to beginning to allow overlapping sounds
            audio.currentTime = 0;
            
            // Apply volume override if provided
            if (volume !== null) {
                audio.volume = Math.max(0, Math.min(1, volume));
            }
            
            // Play the sound (non-blocking)
            audio.play().catch(error => {
                // Silently ignore autoplay policy errors
                if (error.name !== 'NotAllowedError') {
                    console.error(`SoundService: Error playing ${soundName}:`, error);
                }
            });
        } catch (error) {
            console.error(`SoundService: Failed to play ${soundName}:`, error);
        }
    },
    
    /**
     * Toggle mute state
     * @returns {boolean} New mute state
     */
    toggleMute() {
        this.isMuted = !this.isMuted;
        localStorage.setItem('proximity_sound_muted', this.isMuted.toString());
        console.log(`🔊 SoundService: ${this.isMuted ? 'Muted' : 'Unmuted'}`);
        return this.isMuted;
    },
    
    /**
     * Set mute state explicitly
     * @param {boolean} muted - True to mute, false to unmute
     */
    setMute(muted) {
        this.isMuted = !!muted;
        localStorage.setItem('proximity_sound_muted', this.isMuted.toString());
        console.log(`🔊 SoundService: ${this.isMuted ? 'Muted' : 'Unmuted'}`);
    },
    
    /**
     * Get current mute state
     * @returns {boolean} True if muted
     */
    getMute() {
        return this.isMuted;
    },

    /**
     * Set master volume
     * @param {number} volume - Volume level (0.0 to 1.0)
     */
    setVolume(volume) {
        this.masterVolume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('proximity_sound_volume', this.masterVolume.toString());

        // Update all preloaded sounds
        for (const audio of Object.values(this.sounds)) {
            audio.volume = this.masterVolume;
        }

        console.log(`🔊 SoundService: Volume set to ${Math.round(this.masterVolume * 100)}%`);
    },

    /**
     * Get current master volume
     * @returns {number} Volume level (0.0 to 1.0)
     */
    getVolume() {
        return this.masterVolume;
    },

    /**
     * Apply audio preset
     * @param {string} presetName - Preset name (minimal, standard, immersive)
     */
    applyPreset(presetName) {
        const preset = this.presets[presetName];
        if (!preset) {
            console.warn(`SoundService: Preset "${presetName}" not found`);
            return;
        }

        this.currentPreset = presetName;
        this.setVolume(preset.volume);
        localStorage.setItem('proximity_sound_preset', presetName);

        console.log(`🔊 SoundService: Applied preset "${preset.name}" (${Math.round(preset.volume * 100)}%)`);
    },

    /**
     * Get current preset
     * @returns {string} Current preset name
     */
    getPreset() {
        return this.currentPreset;
    },
    
    /**
     * Start playing a looping sound with fade in
     * @param {string} soundName - Name of the sound to loop
     * @param {number} fadeInDuration - Fade in duration in seconds (default: 2.0)
     */
    startLoop(soundName, fadeInDuration = 2.0) {
        if (!this.isInitialized) {
            console.warn('SoundService: Not initialized');
            return;
        }
        
        if (this.isMuted) {
            console.log(`🔊 SoundService: Loop '${soundName}' not started (muted)`);
            return;
        }
        
        // Stop any existing loop first
        if (this.currentLoop) {
            this.stopLoop(0); // Immediate stop
        }
        
        const audio = this.sounds[soundName];
        if (!audio) {
            console.error(`SoundService: Sound '${soundName}' not found`);
            return;
        }
        
        console.log(`🔊 SoundService: Starting loop '${soundName}' with ${fadeInDuration}s fade in`);
        
        // Setup loop
        audio.loop = true;
        audio.volume = 0;
        audio.currentTime = 0;
        
        try {
            audio.play().then(() => {
                // Fade in smoothly
                const steps = 60; // 60 steps for smooth fade
                const stepDuration = (fadeInDuration * 1000) / steps;
                const volumeStep = 0.6 / steps; // Target volume 0.6 for ambient background
                let currentStep = 0;
                
                this.fadeInterval = setInterval(() => {
                    currentStep++;
                    audio.volume = Math.min(0.6, volumeStep * currentStep);
                    
                    if (currentStep >= steps) {
                        clearInterval(this.fadeInterval);
                        this.fadeInterval = null;
                        console.log(`🔊 SoundService: Loop '${soundName}' fade in complete`);
                    }
                }, stepDuration);
                
                this.currentLoop = audio;
            }).catch(error => {
                console.error(`SoundService: Failed to start loop '${soundName}':`, error);
            });
        } catch (error) {
            console.error(`SoundService: Error starting loop '${soundName}':`, error);
        }
    },
    
    /**
     * Stop the current looping sound with fade out
     * @param {number} fadeOutDuration - Fade out duration in seconds (default: 2.0)
     * @returns {Promise} Resolves when fade out is complete
     */
    stopLoop(fadeOutDuration = 2.0) {
        return new Promise((resolve) => {
            if (!this.currentLoop) {
                console.log('🔊 SoundService: No loop to stop');
                resolve();
                return;
            }
            
            // Clear any ongoing fade interval
            if (this.fadeInterval) {
                clearInterval(this.fadeInterval);
                this.fadeInterval = null;
            }
            
            const audio = this.currentLoop;
            
            if (fadeOutDuration === 0) {
                // Immediate stop
                audio.pause();
                audio.currentTime = 0;
                audio.loop = false;
                this.currentLoop = null;
                console.log('🔊 SoundService: Loop stopped immediately');
                resolve();
                return;
            }
            
            console.log(`🔊 SoundService: Stopping loop with ${fadeOutDuration}s fade out`);
            
            const startVolume = audio.volume;
            const steps = 60; // 60 steps for smooth fade
            const stepDuration = (fadeOutDuration * 1000) / steps;
            const volumeStep = startVolume / steps;
            let currentStep = 0;
            
            this.fadeInterval = setInterval(() => {
                currentStep++;
                audio.volume = Math.max(0, startVolume - (volumeStep * currentStep));
                
                if (currentStep >= steps || audio.volume === 0) {
                    clearInterval(this.fadeInterval);
                    this.fadeInterval = null;
                    audio.pause();
                    audio.currentTime = 0;
                    audio.loop = false;
                    this.currentLoop = null;
                    console.log('🔊 SoundService: Loop fade out complete');
                    resolve();
                }
            }, stepDuration);
        });
    },
    
    /**
     * Test all sounds (useful for debugging)
     * Plays all sounds in sequence with 500ms delay
     */
    testAllSounds() {
        console.log('🔊 SoundService: Testing all sounds...');
        const soundNames = Object.keys(this.soundFiles);
        let index = 0;
        
        const playNext = () => {
            if (index < soundNames.length) {
                const soundName = soundNames[index];
                console.log(`   Playing: ${soundName}`);
                this.play(soundName);
                index++;
                setTimeout(playNext, 600); // 600ms delay between sounds
            } else {
                console.log('🔊 SoundService: Test complete');
            }
        };
        
        playNext();
    }
};
