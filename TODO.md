# 🎯 Proximity: The Ultimate Master Plan

**Status:** 🔴 EPIC 0 IN PROGRESS  
**Current Focus:** OPERAZIONE STABILITÀ TOTALE  
**Last Updated:** October 16, 2025

---

## 🚨 EPIC 0: "OPERAZIONE STABILITÀ TOTALE" (CURRENT - TOP PRIORITY)

**Rationale:** Non si costruisce un grattacielo su fondamenta di sabbia. Dobbiamo avere fiducia al 150% nella codebase attuale prima di aggiungere un solo `div` nuovo.

**📚 Full Documentation:** See `EPIC_0_MASTER_PLAN.md` for complete details  
**⚡ Quick Reference:** See `EPIC_0_QUICK_REFERENCE.md` for commands  
**🔧 Automation:** Use `./epic0_quick_start.sh` for quick testing

### Core Objectives:
1. ✅ **100% Backend Test Pass Rate** (259/259 tests)
2. ✅ **100% E2E Test Reliability** (Zero flaky tests)
3. ✅ **Complete Critical Flow Coverage**
4. ✅ **Real Proxmox Integration Validation**

### Progress Tracking:
- [ ] **PILLAR 1:** Backend Test Perfection
  - [ ] Fix Clone/Config tests (test_app_clone_config.py)
  - [ ] Eliminate RuntimeWarnings (async/await issues)
  - [ ] Achieve 100% pass rate (259/259)
  
- [ ] **PILLAR 2:** E2E Test Reliability
  - [ ] Eliminate TargetClosedError
  - [ ] Strengthen Auth Fixture (7-layer wait strategy)
  - [ ] Fix Navigation Test Stability
  
- [ ] **PILLAR 3:** Critical Flow Coverage
  - [ ] Create test_full_lifecycle.py
  - [ ] Create test_backup_restore.py
  - [ ] Create test_app_update.py
  
- [ ] **PILLAR 4:** Real Integration Validation
  - [ ] Create tests/integration/test_proxmox_real.py
  - [ ] Setup test environment
  - [ ] Run against dev Proxmox instance

### Success Criteria:
```
✅ 259/259 backend tests passing, 0 warnings
✅ 100% E2E pass rate on critical flows
✅ 10 consecutive full test runs with 0 failures
✅ Proxmox integration tests passing
✅ Complete documentation generated
```

**⚠️ BLOCCO ASSOLUTO:** No new features until EPIC 0 is 100% complete!

---

#### **EPIC 1: LA "GENESIS RELEASE" (Completamento v1.0)**
*   **Rationale:** Finalizzare tutte le feature "must-have" che definiscono l'esperienza Proximity di base, rendendola un prodotto completo e affidabile.
*   **Subtasks:**
    1.  `[ ]` **IMPLEMENT-FEATURE-CLONE-APP:** Finalizzare la logica di backend, UI e test E2E per la clonazione delle app (feature PRO).
    2.  `[ ]` **IMPLEMENT-FEATURE-CONFIG-EDIT:** Finalizzare la logica di backend, UI e test E2E per la modifica della configurazione post-deploy (feature PRO).
    3.  `[ ]` **IMPLEMENT-FEATURE-AUTO-BACKUPS:** Creare lo `SchedulerService` per eseguire i backup automatici in modalità `AUTO`.
    4.  `[ ]` **IMPLEMENT-FEATURE-AUTO-UPDATE-CHECK:** Implementare nello scheduler il check periodico di nuove versioni delle app.
    5.  `[ ]` **FEATURE-ADOPT-CONTAINER:** Implementare il "Discovery Wizard" per importare e gestire LXC/VM esistenti.
        *   Creare lo script di discovery (magari nell'alpine temporanea in ramdisk).
        *   Sviluppare la UI e l'API di "adozione".

---

#### **EPIC 2: "OPERAZIONE GIOIELLINO" (Polish & UX "Wow")**
*   **Rationale:** Trasformare un'applicazione funzionale in un'esperienza memorabile e piacevole da usare. Questo è ciò che genera "amore" per il brand.
*   **Subtasks:**
    1.  `[ ]` **UX-ONBOARDING-POWER-ON:** Implementare la schermata di avvio iniziale con il pulsante di accensione.
    2.  `[ ]` **UX-SOUND-SYSTEM:** Implementare il `SoundService` e integrare i feedback audio in tutta la UI.
    3.  `[ ]` **UX-THEME-ENGINE-CORE:** Creare l'infrastruttura per le "skin" (caricamento di CSS custom).
    4.  `[ ]` **UX-THEME-IMPLEMENTATION:** Implementare i primi 2-3 temi che hai disegnato (es. "Arc Reactor", "Crimson Circuit").
    5.  `[ ]` **UX-RACK-NAVIGATION:** Eseguire il refactoring della navigazione per trasformarla nel "Rack Proximity" con il "display LCD" per le notifiche.
    6.  `[ ]` **UX-RACK-FLIP:** Implementare l'animazione per "girare" le card e mostrare il "retro del rack" con i dati di rete.

---

#### **EPIC 3: L'ECOSISTEMA APERTO ("The Platform")**
*   **Rationale:** Aprire Proximity alla community, trasformandolo da prodotto a piattaforma estensibile. Questo è il motore della crescita a lungo termine.
*   **Subtasks:**
    1.  `[ ]` **FEATURE-WIDGET-ENGINE:** Creare l'infrastruttura per la dashboard personalizzabile.
    2.  `[ ]` **WIDGETS-INITIAL-SET:** Sviluppare 2-3 widget di default (Uptime Kuma, Pi-hole, RSS).
    3.  `[ ]` **FEATURE-THEMATIC-RACKS:** Implementare la logica per gestire i "Rack Tematici" (Multimedia, Rete, News).
    4.  `[ ]` **FEATURE-COMMUNITY-CHAT-CORE:** Deployare e configurare l'LXC con il server Matrix.
    5.  `[ ]` **FEATURE-COMMUNITY-CHAT-UI:** Creare il "Rack di Comunicazione" con il client Matrix integrato e "skinnato".
    6.  `[ ]` **FEATURE-CUSTOM-CATALOGS:** Implementare la UI e la logica di backend per aggiungere App Store da repo Git esterni.

---

#### **EPIC 4: LA FORTEZZA AUTONOMA (Architettura & Sicurezza Avanzata)**
*   **Rationale:** Implementare le "bombe" architetturali che rendono Proximity un sistema di livello enterprise in termini di sicurezza e gestione.
*   **Subtasks:**
    1.  `[ ]` **ARCH-MICRO-LXC:** (Opzionale) Valutare se splittare l'Appliance monolitico in LXC dedicati, se la complessità lo richiede.
    2.  `[ ]` **FEATURE-VPN-GATEWAY:** Integrare WireGuard nell'Appliance per l'accesso remoto sicuro e il DNS magico `.prox`.
    3.  `[ ]` **FEATURE-EGRESS-GUARDIAN:** Integrare Squid/AdGuard per il controllo del traffico in uscita.
    4.  `[ ]` **FEATURE-GITOPS-CORE:** Implementare il sistema di stato basato su repository Git "bare" e il `ReconciliationService`.
    5.  `[ ]` **REFACTOR-STATE-TO-GITOPS:** Eseguire il refactoring profondo per rendere tutte le operazioni `git commit`-driven.

---

#### **EPIC 5: LA PIATTAFORMA INTELLIGENTE (AI & ML)**
*   **Rationale:** Portare Proximity al livello successivo, rendendolo un partner proattivo e conversazionale.
*   **Subtasks:**
    1.  `[ ]` **FEATURE-AI-AGENT-LXC:** Creare un LXC di sistema opzionale per ospitare l'LLM locale (`qwen`).
    2.  `[ ]` **FEATURE-OMNI-PROMPT-UI:** Trasformare il "display LCD" nel "Command/Conversation Box" unificato.
    3.  `[ ]` **FEATURE-AI-INTENT-ROUTER:** Sviluppare il router di intenti che instrada l'input alla CLI, all'AI o alla Chat.
    4.  `[ ]` **FEATURE-AI-MCP:** Costruire il Model-Control-Plane con i "tool" che l'AI può usare per interrogare e gestire Proximity.
    5.  `[ ]` **FEATURE-AUTOSCALING-ML:** Integrare il tuo motore di autoscaling ML esistente.

---

#### **EPIC 6: L'ECOSISTEMA DISTRIBUITO (Il Sogno Finale)**
*   **Rationale:** Trascendere il singolo server e creare una rete globale.
*   **Subtasks:**
    1.  `[ ]` **ARCH-DOCKERIZE-PROXIMITY:** Creare l'immagine Docker ufficiale di Proximity.
    2.  `[ ]` **FEATURE-MULTI-CLUSTER:** Estendere il sistema per gestire più host Proxmox remoti.
    3.  `[ ]` **FEATURE-FEDERATION:** Implementare il workflow GitOps su `proximity.host` per il discovery dei peer e la rete mesh WireGuard.

Questo è il piano completo. È immenso, ma ogni Epic si costruisce sul precedente. La nostra missione, ora, è **conquistare l'EPIC 0.**