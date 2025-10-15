# 🚀 Guida Esecuzione Test Pulsanti My Apps

## 📋 Prerequisiti

Prima di eseguire i test, assicurati che:

1. ✅ **Playwright browsers installati** (già fatto)
2. ⏳ **Server backend in esecuzione**
3. ⏳ **Almeno 1 app deployata nel sistema**

---

## 🔧 Setup Completo

### Step 1: Avvia il Backend

```bash
# Naviga alla cartella backend
cd /Users/fab/GitHub/proximity/backend

# Avvia il server
python main.py
```

**Output Atteso**:
```
INFO:     Uvicorn running on http://0.0.0.0:8765 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Verifica Server Attivo

Apri un nuovo terminale e verifica:

```bash
curl http://localhost:8765/api/health
```

**Output Atteso**:
```json
{"status":"healthy"}
```

### Step 3: Verifica Presenza App

```bash
# Login e ottieni token (sostituisci con le tue credenziali)
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Ottieni lista app (usa il token ricevuto)
curl http://localhost:8765/api/v1/apps \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Output Atteso**: Lista di app deployate (almeno 1)

---

## 🧪 Esecuzione Test

### Opzione 1: Test Completo (Tutti i 15 Test)

```bash
cd /Users/fab/GitHub/proximity
pytest test_my_apps_actions.py -v -s
```

### Opzione 2: Test Singolo

```bash
# Testa solo il pulsante delete
pytest test_my_apps_actions.py::TestMyAppsActions::test_14_delete_button_opens_modal -v -s

# Testa solo i pulsanti start/stop
pytest test_my_apps_actions.py::TestMyAppsActions::test_01_toggle_status_stop -v -s
pytest test_my_apps_actions.py::TestMyAppsActions::test_02_toggle_status_start -v -s

# Testa solo i pulsanti PRO
pytest test_my_apps_actions.py::TestMyAppsActions::test_11_clone_pro_feature -v -s
pytest test_my_apps_actions.py::TestMyAppsActions::test_12_edit_config_pro_feature -v -s
```

### Opzione 3: Test con Report HTML

```bash
pytest test_my_apps_actions.py -v -s --html=test_report.html --self-contained-html
```

### Opzione 4: Test in Modalità Headful (Vedi Browser)

Modifica temporaneamente `test_my_apps_actions.py`:

```python
@pytest.fixture(autouse=True)
def setup(self, page: Page):
    # Aggiungi questa riga all'inizio per vedere il browser
    page.context.set_default_timeout(10000)
    # ... resto del codice
```

Poi esegui con:
```bash
pytest test_my_apps_actions.py -v -s --headed
```

---

## 📊 Interpretazione Risultati

### Output di Successo ✅

```
test_my_apps_actions.py::TestMyAppsActions::test_01_toggle_status_stop[chromium] PASSED
test_my_apps_actions.py::TestMyAppsActions::test_02_toggle_status_start[chromium] PASSED
test_my_apps_actions.py::TestMyAppsActions::test_03_open_external[chromium] PASSED
...
test_my_apps_actions.py::TestMyAppsActions::test_15_all_buttons_present[chromium] PASSED

============================== 15 passed in 45.23s ==============================
```

### Output con Skip ⚠️

```
test_my_apps_actions.py::TestMyAppsActions::test_03_open_external[chromium] SKIPPED
Reason: Open External button is disabled (no URL or app not running)
```

**Questo è OK**: Alcuni test vengono skippati se le condizioni non sono soddisfatte (es. app non ha URL)

### Output di Errore ❌

```
test_my_apps_actions.py::TestMyAppsActions::test_04_view_logs[chromium] FAILED
E   playwright._impl._errors.Error: Timeout 10000ms exceeded
```

**Possibili Cause**:
- Modal non si apre
- Selettore non corretto
- Problema nel codice frontend

---

## 🔍 Debug dei Test

### Attiva Logging Dettagliato

```bash
pytest test_my_apps_actions.py -v -s --log-cli-level=DEBUG
```

### Screenshot su Errore

Aggiungi al test:

```python
@pytest.fixture(autouse=True)
def setup(self, page: Page):
    yield page
    # Screenshot se test fallisce
    if hasattr(self, '_outcome') and self._outcome.errors:
        page.screenshot(path=f"error_{test_name}.png")
```

### Video Recording

Modifica `conftest.py` o crea uno:

```python
@pytest.fixture(scope="function")
def context(browser):
    context = browser.new_context(
        record_video_dir="videos/",
        record_video_size={"width": 1280, "height": 720}
    )
    yield context
    context.close()
```

---

## 📈 Metriche e Report

### Coverage Report

```bash
pytest test_my_apps_actions.py --cov=backend/frontend/js --cov-report=html
```

### Test Timing

```bash
pytest test_my_apps_actions.py -v --durations=10
```

### Test Summary

```bash
pytest test_my_apps_actions.py -v --tb=short --maxfail=1
```

---

## 🚨 Troubleshooting

### Problema: "ERR_CONNECTION_REFUSED"

**Causa**: Server non in esecuzione

**Soluzione**:
```bash
cd backend && python main.py
```

### Problema: "No running app available for testing"

**Causa**: Nessuna app in stato "running"

**Soluzione**:
1. Deploya un'app dal catalogo
2. Oppure avvia un'app esistente tramite UI

### Problema: "Login failed"

**Causa**: Credenziali errate

**Soluzione**: Verifica username/password in `test_my_apps_actions.py`:
```python
TEST_USERNAME = "admin"  # Cambia se necessario
TEST_PASSWORD = "admin"  # Cambia se necessario
```

### Problema: "Timeout waiting for selector"

**Causa**: Elemento non trovato o caricamento lento

**Soluzione**: Aumenta timeout in `test_my_apps_actions.py`:
```python
page.wait_for_selector('.app-card.deployed', timeout=30000)  # Da 10000 a 30000
```

### Problema: Test intermittenti

**Causa**: Timing issues

**Soluzione**: Aggiungi wait espliciti:
```python
page.wait_for_timeout(1000)  # Attendi 1 secondo
page.wait_for_load_state("networkidle")  # Attendi rete inattiva
```

---

## 🎯 Scenari di Test Specifici

### Test Solo Pulsanti Base (Non PRO)

```bash
pytest test_my_apps_actions.py -k "not pro_feature" -v -s
```

### Test Solo Pulsanti PRO

```bash
pytest test_my_apps_actions.py -k "pro_feature" -v -s
```

### Test Solo Modal

```bash
pytest test_my_apps_actions.py -k "modal or logs or console or backup or volume" -v -s
```

### Test Solo Azioni App Control

```bash
pytest test_my_apps_actions.py -k "toggle or restart or delete" -v -s
```

---

## 📝 Checklist Pre-Test

- [ ] Backend server running (localhost:8765)
- [ ] Almeno 1 app deployata
- [ ] Almeno 1 app in stato "running" (per test completi)
- [ ] App con URL configurato (per test open external)
- [ ] Credenziali corrette in test file
- [ ] Playwright browsers installati

---

## 🚀 Quick Start (Tutto in Uno)

```bash
# Terminal 1: Avvia Backend
cd /Users/fab/GitHub/proximity/backend && python main.py

# Terminal 2: Esegui Test (dopo che backend è pronto)
cd /Users/fab/GitHub/proximity
sleep 5  # Aspetta che il server sia pronto
pytest test_my_apps_actions.py -v -s

# Se tutto passa, vedrai:
# ============================== 15 passed in 45.23s ==============================
```

---

## 📊 Risultati Attesi

### Scenario Ideale (15/15 PASSED)

```
✅ test_01_toggle_status_stop       → App fermata correttamente
✅ test_02_toggle_status_start      → App avviata correttamente  
✅ test_03_open_external            → Nuova tab aperta
✅ test_04_view_logs                → Modal logs aperto
✅ test_05_console                  → Modal console aperto
✅ test_06_backups                  → Modal backup aperto
✅ test_07_volumes                  → Modal volumes aperto
✅ test_08_monitoring               → Modal monitoring aperto
✅ test_09_restart                  → App riavviata
✅ test_10_update                   → Modal update aperto
✅ test_11_clone_pro_feature        → Modal clone/PRO aperto
✅ test_12_edit_config_pro_feature  → Modal config/PRO aperto
✅ test_13_canvas                   → Canvas view aperta
✅ test_14_delete_button_opens_modal → Modal delete aperto
✅ test_15_all_buttons_present      → Tutti i pulsanti trovati
```

### Scenario Realistico (12-15 PASSED, 0-3 SKIPPED)

Alcuni test potrebbero essere skipped in base allo stato delle app:
- `test_03_open_external` → SKIPPED se app non ha URL
- `test_08_monitoring` → SKIPPED se app non running
- `test_13_canvas` → SKIPPED se app non ha iframe_url

**Questo è normale e accettabile!**

---

## 📚 Riferimenti

- **Test File**: `test_my_apps_actions.py`
- **Report Completo**: `MY_APPS_BUTTONS_VERIFICATION_REPORT.md`
- **Riepilogo**: `MY_APPS_BUTTONS_SUMMARY.md`
- **Diagramma**: `MY_APPS_BUTTONS_VISUAL.txt`

---

**Data**: 15 Ottobre 2025  
**Stato Prerequisiti**: Playwright ✅ | Server ⏳ | App ⏳  
**Pronto per Esecuzione**: Quando server e app sono disponibili
