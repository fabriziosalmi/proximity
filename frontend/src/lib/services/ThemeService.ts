/**
 * ThemeService - Dynamic Theme Switching for Proximity 2.0
 * 
 * This service manages application themes dynamically by loading
 * CSS files and applying them to the document head.
 * 
 * Features:
 * - Dynamic CSS injection
 * - LocalStorage persistence
 * - Multiple theme support
 * - Singleton pattern
 */

export interface Theme {
	id: string;
	name: string;
	description: string;
	cssPath: string;
}

class ThemeServiceClass {
	private currentTheme: string = 'dark';
	private readonly STORAGE_KEY = 'proximity_theme';
	private themeElement: HTMLLinkElement | null = null;

	private themes: Theme[] = [
		{
			id: 'dark',
			name: 'Dark Mode',
			description: 'Professional dark theme with cyan accents (Default)',
			cssPath: '/src/assets/themes/dark_theme.css'
		},
		{
			id: 'light',
			name: 'Light Mode',
			description: 'Clean light theme with blue accents',
			cssPath: '/src/assets/themes/light_theme.css'
		},
		{
			id: 'matrix',
			name: 'Matrix',
			description: 'Cyberpunk-inspired green-on-black theme',
			cssPath: '/src/assets/themes/matrix_theme.css'
		}
	];

	constructor() {
		// Initialize theme from localStorage or default
		if (typeof window !== 'undefined') {
			const saved = localStorage.getItem(this.STORAGE_KEY);
			if (saved && this.themes.find(t => t.id === saved)) {
				this.currentTheme = saved;
			}
		}
	}

	/**
	 * Get all available themes
	 */
	getThemes(): Theme[] {
		return this.themes;
	}

	/**
	 * Get the current active theme ID
	 */
	getCurrentTheme(): string {
		return this.currentTheme;
	}

	/**
	 * Set and apply a new theme
	 * @param themeId - The ID of the theme to apply
	 */
	async setTheme(themeId: string): Promise<void> {
		const theme = this.themes.find(t => t.id === themeId);
		
		if (!theme) {
			console.error(`Theme "${themeId}" not found`);
			return;
		}

		// Remove existing theme link if present
		if (this.themeElement) {
			this.themeElement.remove();
			this.themeElement = null;
		}

		// Create new link element
		this.themeElement = document.createElement('link');
		this.themeElement.rel = 'stylesheet';
		this.themeElement.href = theme.cssPath;
		this.themeElement.id = 'dynamic-theme';

		// Append to head
		document.head.appendChild(this.themeElement);

		// Wait for the stylesheet to load
		await new Promise<void>((resolve) => {
			if (this.themeElement) {
				this.themeElement.onload = () => resolve();
				// Fallback timeout
				setTimeout(resolve, 100);
			} else {
				resolve();
			}
		});

		// Update current theme and persist
		this.currentTheme = themeId;
		
		if (typeof window !== 'undefined') {
			localStorage.setItem(this.STORAGE_KEY, themeId);
		}

		console.log(`✨ Theme switched to: ${theme.name}`);
	}

	/**
	 * Initialize the theme service
	 * This should be called when the app starts
	 */
	async init(): Promise<void> {
		// Apply the saved/default theme
		await this.setTheme(this.currentTheme);
	}

	/**
	 * Get theme details by ID
	 */
	getThemeById(themeId: string): Theme | undefined {
		return this.themes.find(t => t.id === themeId);
	}
}

// Export singleton instance
export const ThemeService = new ThemeServiceClass();
export default ThemeService;
