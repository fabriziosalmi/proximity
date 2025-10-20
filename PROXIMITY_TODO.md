# Proximity 2.0 - Strategic Roadmap & TODO

**Document Version:** 2.1.0
**Last Updated:** October 20, 2025
**Status:** ✅ Genesis Release Complete. Planning Post-Genesis EPICs.

---

## 🎯 Executive Summary

La **"Genesis Release"** è completa. Abbiamo una piattaforma stabile, funzionale e raffinata. Questa roadmap definisce i prossimi EPIC strategici per evolvere Proximity 2.0 da un eccellente "LXC Manager" a una vera e propria "Piattaforma di Cloud Personale".

Ogni EPIC è un blocco di valore autoconsistente.

---

### **🔴 EPIC ATTUALE: NESSUNO. Fase di pianificazione strategica.**

---

## 🚀 EPIC 6: "The Open Ecosystem" (Priorità: ALTA)

**Visione:** Trasformare Proximity da prodotto a piattaforma, sbloccando la personalizzazione e il contributo della community. (Pilastri: "Ecosistema Aperto", "Divertimento")

| Dominio | Task | Priorità | Note |
|---|---|---|---|
| **UI/UX** | **Implementare la UI per il Theme Switcher** | ALTA | Il `ThemeService` è pronto. Serve un dropdown in `/settings` che lo usi. |
| **Backend** | **Costruire il `WidgetEngine`** | ALTA | Definire modelli DB per `WidgetInstance` e `WidgetType`. Creare un'API per CRUD sui widget della dashboard. |
| **Frontend** | **Creare la Dashboard a Widget** | ALTA | Sostituire la dashboard statica con una griglia dinamica (es. `gridstack.js`) dove gli utenti possono aggiungere/rimuovere/ridimensionare i widget. |
| **Frontend** | Sviluppare un set iniziale di Widget (Statistiche, Log Recenti, etc.)| MEDIA | Creare i primi 2-3 componenti widget Svelte riutilizzabili. |
| **Backend** | **Implementare i Cataloghi Git** | MEDIA | Creare un'API e un servizio per aggiungere "App Store" da repository Git esterni. Il `CatalogService` dovrà essere refactorato per gestire sorgenti multiple. |
| **Frontend** | Creare la UI per la gestione dei Cataloghi in `/settings` | BASSA | Un form per aggiungere l'URL di un repo Git. |

---

## ☁️ EPIC 7: "The Distributed Cloud" (Priorità: MEDIA)

**Visione:** Trascendere il singolo server, gestendo flotte di host Proxmox come un unico cloud coeso. (Pilastri: "Casa Digitale", "Tranquillità by Default")

| Dominio | Task | Priorità | Note |
|---|---|---|---|
| **Frontend**| **Evolvere la UI Multi-Host in `/settings`** | ALTA | Trasformare il form di Proxmox in una tabella CRUD per gestire `N` host (Aggiungi, Modifica, Elimina, Testa Connessione). |
| **Backend** | **Creare il `MigrationService`** | ALTA | Implementare la logica per orchestrare una migrazione LXC (offline per ora) tra nodi, anche di host diversi. |
| **Frontend** | Aggiungere il pulsante "Migrate" alla `RackCard` | MEDIA | Al click, deve aprire un modale per selezionare l'host/nodo di destinazione. |
| **Backend** | Sviluppare un "Cluster Balancer" (Celery Beat Task) | BASSA | Un task periodico che analizza il carico su tutti i nodi e genera "raccomandazioni" di bilanciamento. |
| **Docs** | Documentare i requisiti per la migrazione cross-host | MEDIA | (es. storage condiviso, requisiti di rete). |

---

## 🧠 EPIC 8: "The Intelligent Agent" (Priorità: MEDIA-BASSA)

**Visione:** Rendere Proximity un partner proattivo e conversazionale, non solo uno strumento reattivo. (Pilastri: "Divertimento", "Tranquillità by Default")

| Dominio | Task | Priorità | Note |
|---|---|---|---|
| **Backend** | **Creare l'infrastruttura per l'LLM** | ALTA | Definire un `AIAgentService` di base. Ricerca sull'integrazione di un LLM locale (es. Ollama). |
| **Frontend**| **Forgiare la "Omni-Prompt" UI** | ALTA | Trasformare il `SystemStatusLCD` o la barra di ricerca in un input di testo unificato per comandi e conversazioni. |
| **Backend** | **Costruire il "Model-Control-Plane" (MCP)** | MEDIA | Definire un set di "tool" sicuri che l'LLM può chiamare (es. `list_apps`, `get_app_status`). L'AI non deve mai eseguire comandi arbitrari. |
| **Docs** | Definire lo schema per i "tool" AI | MEDIA | Come descrivere le funzioni e i loro parametri all'LLM. |
| **Workflow**| Integrare l'AI nel nostro workflow di testing | BASSA | L'AI può aiutare a generare test o analizzare i fallimenti? |

---

## 🎨 EPIC 9: "The Immersive Canvas" (Progetto Unity) (Priorità: BASSA - R&D)

**Visione:** Realizzare il "salto quantico" finale, trasformando la dashboard in un'esperienza 3D. (Pilastri: "Casa Digitale", "Divertimento")

| Dominio | Task | Priorità | Note |
|---|---|---|---|
| **Workflow**| **Fase di Ricerca e Sviluppo (R&D)** | ALTA | Investigare le tecnologie: Unity, Three.js, Babylon.js. Valutare pro e contro di performance, integrazione, curva di apprendimento. |
| **Frontend**| Creare un Proof of Concept (PoC) | MEDIA | Un singolo componente Svelte che renderizza un cubo 3D con Three.js all'interno del nostro `MainCanvas`. |
| **API** | Progettare un'API WebSocket per lo streaming di dati | MEDIA | La vista 3D necessiterà di un flusso di dati real-time, non di polling. Dobbiamo usare Django Channels. |
| **Docs** | Documentare i risultati della fase R&D | BASSA | Creare un report sulla tecnologia scelta e un piano di implementazione grezzo. |

---

## 🧹 Debito Tecnico & Miglioramenti Incrementali (On-going)

Questa è la lista di task minori da affrontare quando c'è tempo o tra un EPIC e l'altro.

| Dominio | Task | Priorità | Note |
|---|---|---|---|
| **Backend** | **Ottimizzare il Template LXC** | MEDIA | Risolvere il conflitto AppArmor che causa lentezza nello shutdown. |
| **Frontend**| **Rifinitura Finale "Gioiellino"** | MEDIA | Bug E2E del flip, suoni mancanti, piccole inconsistentezze UI. |
| **Backend** | **Rate Limiting & Quotas (#14)** | BASSA | Implementare `django-ratelimit` per la sicurezza in produzione. |
| **Docs** | **Creare `CONTRIBUTING.md`** | BASSA | Fondamentale prima di un vero lancio open-source. |
| **Workflow**| **Impostare la CI/CD Pipeline con GitHub Actions** | ALTA | Automatizzare build, test unitari e test E2E. **Questo è un acceleratore per tutti gli EPIC futuri.** |
| **Backend** | **Application Dependencies (#13)** | BASSA | Aggiungere `depends_on` al catalogo per gestire stack multi-app. |
| **Frontend**| **Bulk Operations UI (#8)** | MEDIA | Aggiungere checkbox alle `RackCard` e una barra per azioni di massa. |