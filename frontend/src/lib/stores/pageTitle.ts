/**
 * Svelte store for managing the current page title.
 * Each page can set its own title dynamically.
 */

import { writable } from 'svelte/store';

function createPageTitleStore() {
	const { subscribe, set } = writable<string>('Proximity');

	return {
		subscribe,
		setTitle: (title: string) => set(title)
	};
}

export const pageTitleStore = createPageTitleStore();
