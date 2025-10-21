/**
 * SoundService - Centralized audio feedback system
 * Provides subtle, futuristic sound effects for UI interactions
 */

export type SoundType = 'click' | 'deploy-start' | 'success' | 'error' | 'flip' | 'backup-create' | 'restore';

interface SoundConfig {
	enabled: boolean;
	volume: number; // 0.0 to 1.0
}

class SoundServiceClass {
	private sounds: Map<SoundType, HTMLAudioElement> = new Map();
	private config: SoundConfig;
	private initialized = false;

	// Sound file paths
	private soundPaths: Record<SoundType, string> = {
		click: '/sounds/click.wav',
		'deploy-start': '/sounds/deploy-start.wav',
		success: '/sounds/success.wav',
		error: '/sounds/error.wav',
		flip: '/sounds/flip.wav',
		'backup-create': '/sounds/backup-create.wav',
		restore: '/sounds/restore.wav'
	};

	constructor() {
		// Load configuration from localStorage
		this.config = this.loadConfig();
	}

	/**
	 * Initialize the sound service (load audio files)
	 * Call this once when the app starts
	 */
	public init(): void {
		if (this.initialized || typeof window === 'undefined') return;

		try {
			// Preload all sound files
			Object.entries(this.soundPaths).forEach(([soundType, path]) => {
				const audio = new Audio(path);
				audio.volume = this.config.volume;
				audio.preload = 'auto';

				// Handle loading errors gracefully - suppress console warnings
				audio.addEventListener('error', () => {
					// Silently fail - sounds are optional UI enhancement
					// Remove the sound from the map so we don't try to play it
					this.sounds.delete(soundType as SoundType);
				});

				this.sounds.set(soundType as SoundType, audio);
			});

			this.initialized = true;
			// Only log if we successfully loaded at least one sound
			if (this.sounds.size > 0) {
				console.log('[SoundService] Initialized with', this.sounds.size, 'sound(s)');
			}
		} catch (error) {
			console.error('[SoundService] Initialization error:', error);
		}
	}

	/**
	 * Play a sound effect
	 */
	public play(soundType: SoundType): void {
		if (!this.config.enabled) return;
		if (!this.initialized) this.init();

		const sound = this.sounds.get(soundType);
		if (!sound) {
			// Silently skip if sound file doesn't exist
			return;
		}

		try {
			// Reset to start if already playing
			sound.currentTime = 0;
			sound.volume = this.config.volume;

			// Play the sound (catch promise rejection for browsers that block autoplay)
			const playPromise = sound.play();
			if (playPromise !== undefined) {
				playPromise.catch(() => {
					// Silently fail - autoplay blocked or other playback issue
				});
			}
		} catch (error) {
			// Silently fail - sounds are optional
		}
	}

	/**
	 * Enable or disable sounds
	 */
	public setEnabled(enabled: boolean): void {
		this.config.enabled = enabled;
		this.saveConfig();
	}

	/**
	 * Check if sounds are enabled
	 */
	public isEnabled(): boolean {
		return this.config.enabled;
	}

	/**
	 * Set volume (0.0 to 1.0)
	 */
	public setVolume(volume: number): void {
		this.config.volume = Math.max(0, Math.min(1, volume));
		this.saveConfig();

		// Update volume for all loaded sounds
		this.sounds.forEach((audio) => {
			audio.volume = this.config.volume;
		});
	}

	/**
	 * Get current volume
	 */
	public getVolume(): number {
		return this.config.volume;
	}

	/**
	 * Load configuration from localStorage
	 */
	private loadConfig(): SoundConfig {
		if (typeof window === 'undefined') {
			return { enabled: true, volume: 0.3 };
		}

		try {
			const saved = localStorage.getItem('proximity_sound_config');
			if (saved) {
				const parsed = JSON.parse(saved);
				return {
					enabled: parsed.enabled !== false, // Default to true
					volume: typeof parsed.volume === 'number' ? parsed.volume : 0.3
				};
			}
		} catch (error) {
			console.warn('[SoundService] Failed to load config:', error);
		}

		return { enabled: true, volume: 0.3 };
	}

	/**
	 * Save configuration to localStorage
	 */
	private saveConfig(): void {
		if (typeof window === 'undefined') return;

		try {
			localStorage.setItem('proximity_sound_config', JSON.stringify(this.config));
		} catch (error) {
			console.warn('[SoundService] Failed to save config:', error);
		}
	}

	/**
	 * Test a sound (useful for settings UI)
	 */
	public test(soundType: SoundType): void {
		const wasEnabled = this.config.enabled;
		this.config.enabled = true;
		this.play(soundType);
		this.config.enabled = wasEnabled;
	}
}

// Export singleton instance
export const SoundService = new SoundServiceClass();
