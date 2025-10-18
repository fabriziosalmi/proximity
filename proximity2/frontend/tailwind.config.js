/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			colors: {
				// Custom color palette for the "Rack Proximity" theme
				rack: {
					primary: '#00d4ff',
					secondary: '#7000ff',
					accent: '#ff00d4',
					dark: '#0a0e1a',
					darker: '#050810',
					light: '#1a1f35',
					glow: 'rgba(0, 212, 255, 0.3)'
				}
			},
			boxShadow: {
				glow: '0 0 20px var(--glow-color, rgba(0, 212, 255, 0.3))',
				'glow-lg': '0 0 40px var(--glow-color, rgba(0, 212, 255, 0.5))'
			},
			animation: {
				'pulse-glow': 'pulse-glow 2s ease-in-out infinite'
			},
			keyframes: {
				'pulse-glow': {
					'0%, 100%': { opacity: 1 },
					'50%': { opacity: 0.5 }
				}
			}
		}
	},
	plugins: []
};
