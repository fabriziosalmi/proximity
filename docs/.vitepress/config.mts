import { defineConfig } from 'vitepress'

// Template VitePress con generazione sitemap automatica e SEO ottimizzato
// Sostituisci i placeholder:
// proximity: nome esatto del repository GitHub (es. open-bpm)
// Proximity: Titolo leggibile del progetto (es. OpenBPM)
// An immersive management layer for Proxmox based personal infrastructure.: Descrizione concisa per SEO e Open Graph
// fabriziosalmi: fabriziosalmi

export default defineConfig({
  title: 'Proximity',
  description: 'An immersive management layer for Proxmox based personal infrastructure.',
  base: '/proximity/',
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: true,
  srcExclude: ['**/archive/**'],

  // SITEMAP AUTOMATICO
  // Genera automaticamente sitemap.xml in fase di build con tutti gli URL indicizzati
  sitemap: {
    hostname: 'https://fabriziosalmi.github.io/proximity/',
  },

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/proximity/favicon.svg' }],
    ['link', { rel: 'apple-touch-icon', href: '/proximity/favicon.svg' }],
    ['link', { rel: 'canonical', href: 'https://fabriziosalmi.github.io/proximity/' }],
    ['meta', { name: 'theme-color', content: '#10b981' }],
    ['meta', { name: 'color-scheme', content: 'dark light' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:title', content: 'Proximity' }],
    ['meta', { property: 'og:description', content: 'An immersive management layer for Proxmox based personal infrastructure.' }],
    ['meta', { property: 'og:url', content: 'https://fabriziosalmi.github.io/proximity/' }],
    ['meta', { property: 'og:image', content: 'https://fabriziosalmi.github.io/proximity/favicon.svg' }],
    ['meta', { name: 'twitter:card', content: 'summary' }],
    ['meta', { name: 'twitter:title', content: 'Proximity' }],
    ['meta', { name: 'twitter:description', content: 'An immersive management layer for Proxmox based personal infrastructure.' }],
    ['meta', { name: 'twitter:image', content: 'https://fabriziosalmi.github.io/proximity/favicon.svg' }],
    ['meta', { name: 'robots', content: 'index, follow, max-image-preview:large' }],
    [
      'script',
      { type: 'application/ld+json' },
      JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': [
          {
            '@type': 'SoftwareApplication',
            '@id': 'https://fabriziosalmi.github.io/proximity/#software',
            name: 'Proximity',
            operatingSystem: 'Cross-platform',
            applicationCategory: 'DeveloperApplication',
            description: 'An immersive management layer for Proxmox based personal infrastructure.',
            url: 'https://fabriziosalmi.github.io/proximity/',
            license: 'https://opensource.org/licenses/MIT',
            codeRepository: 'https://github.com/fabriziosalmi/proximity',
            author: {
              '@type': 'Person',
              name: 'Fabrizio Salmi',
              url: 'https://github.com/fabriziosalmi',
            },
          },
          {
            '@type': 'WebSite',
            '@id': 'https://fabriziosalmi.github.io/proximity/#website',
            url: 'https://fabriziosalmi.github.io/proximity/',
            name: 'Proximity Documentation',
            description: 'An immersive management layer for Proxmox based personal infrastructure.',
            publisher: {
              '@type': 'Person',
              name: 'Fabrizio Salmi',
              url: 'https://github.com/fabriziosalmi',
            },
            inLanguage: 'en-US',
          },
        ],
      }),
    ],
  ],

  themeConfig: {
    siteTitle: 'Proximity',

    nav: [
      { text: 'Documentation', link: '/overview', activeMatch: '/(overview|guides|INSTALLATION|FIRST_STEPS)/' },
      { text: 'Architecture', link: '/ARCHITECTURE', activeMatch: '/(ARCHITECTURE|STRUCTURE)/' },
      { text: 'REST API', link: '/API', activeMatch: '/API' },
      { text: 'Security', link: '/security/BACKEND_SECURITY_AUDIT_REPORT', activeMatch: '/security/' },
      { text: 'GitHub', link: 'https://github.com/fabriziosalmi/proximity' },
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Documentation Map', link: '/overview' },
          { text: 'Quick Start (Docker)', link: '/guides/QUICK_START' },
          { text: 'Installation Guide', link: '/INSTALLATION' },
          { text: 'First Steps & Walkthrough', link: '/FIRST_STEPS' },
        ],
      },
      {
        text: 'Architecture & Design',
        items: [
          { text: 'System Architecture', link: '/ARCHITECTURE' },
          { text: 'Project Structure', link: '/STRUCTURE' },
        ],
      },
      {
        text: 'API & Development',
        items: [
          { text: 'REST API Reference', link: '/API' },
          { text: 'Testing & QA', link: '/TESTING' },
        ],
      },
      {
        text: 'Security & Audits',
        items: [
          { text: 'Backend Security Audit', link: '/security/BACKEND_SECURITY_AUDIT_REPORT' },
          { text: 'Frontend Security Audit', link: '/security/FRONTEND_SECURITY_AUDIT_REPORT' },
        ],
      },
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/fabriziosalmi/proximity' },
    ],

    search: {
      provider: 'local',
      options: {
        detailedView: true,
      },
    },

    outline: {
      level: [2, 3],
      label: 'On this page',
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © Fabrizio Salmi',
    },

    docFooter: {
      prev: 'Previous',
      next: 'Next',
    },
  },

  markdown: {
    theme: {
      light: 'github-light',
      dark: 'github-dark',
    },
  },
})
