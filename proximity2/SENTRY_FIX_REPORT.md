# Sentry Integration - Risoluzione Problema

## 🐛 Problema Riscontrato

**Sintomo:** Vedi traces in Sentry ma non vedi nulla nei feed, logs o errors.

## 🔍 Causa Root

La configurazione Sentry in `settings.py` aveva un filtro `before_send` che **blocca gli eventi quando `DEBUG=True`** a meno che `SENTRY_DEBUG=True` non sia esplicitamente configurato.

```python
# settings.py linea 182
before_send=lambda event, hint: event if not DEBUG or os.getenv('SENTRY_DEBUG', 'False') == 'True' else None,
```

**Perché le traces funzionavano:**
- Le performance transactions (traces) non passano attraverso il filtro `before_send`
- Gli eventi (errors, messages, breadcrumbs, logs) vengono filtrati e scartati

## ✅ Soluzione Applicata

Aggiunta della variabile d'ambiente `SENTRY_DEBUG=True` in `docker-compose.yml` per tutti i servizi backend:

```yaml
# Backend Service
- SENTRY_DEBUG=True

# Celery Worker
- SENTRY_DEBUG=True

# Celery Beat
- SENTRY_DEBUG=True
```

## 📊 Risultati

Dopo il riavvio dei container:

1. ✅ Eventi inviati correttamente a Sentry
2. ✅ Errors catturati e inviati
3. ✅ Messages inviati
4. ✅ Breadcrumbs inclusi
5. ✅ User context arricchito
6. ✅ Transactions & traces funzionanti

## ⚠️ Note Aggiuntive

### Rate Limiting
Sentry sta applicando rate limiting perché stai probabilmente usando il piano gratuito:
```
[sentry] WARNING: Rate-limited via x-sentry-rate-limits
```

**Soluzioni:**
- Riduci `SENTRY_TRACES_SAMPLE_RATE` a `0.1` (10%) per limitare le transactions
- Aggiungi filtri per escludere richieste health check
- Considera upgrade del piano Sentry se necessario

### Missing Release
Alcuni eventi mostrano:
```
[sentry] INFO: Discarded session update because of missing release
```

**Soluzione (opzionale):**
Aggiungi release version in `settings.py`:
```python
sentry_sdk.init(
    dsn=SENTRY_DSN,
    release="proximity@2.0.0",  # Aggiungi questa riga
    ...
)
```

## 🧪 Come Testare

```bash
# Test rapido
./test_sentry_quick.sh

# Test manuale
docker exec proximity2_backend python /app/scripts/test_sentry_integration.py

# Verifica variabili d'ambiente
docker exec proximity2_backend env | grep -E "SENTRY|DEBUG"

# Controlla logs
docker logs proximity2_backend --tail=50 2>&1 | grep -i sentry
```

## 🔗 Dashboard Sentry

Controlla i tuoi eventi su:
- **Issues:** https://sentry.io/organizations/fabriziosalmi/issues/
- **Performance:** https://sentry.io/organizations/fabriziosalmi/performance/

## 📝 Modifiche ai File

1. ✅ `docker-compose.yml` - Aggiunto `SENTRY_DEBUG=True` per backend, celery_worker, celery_beat
2. ✅ `.env.example` - Aggiunto commento su `SENTRY_DEBUG`
3. ✅ `test_sentry_quick.sh` - Nuovo script di test rapido

## 🎯 Prossimi Passi (Opzionali)

1. **Ottimizza Sampling:**
   ```yaml
   - SENTRY_TRACES_SAMPLE_RATE=0.1  # Riduci a 10% per evitare rate limiting
   ```

2. **Aggiungi Release:**
   ```python
   release="proximity@2.0.0"
   ```

3. **Filtra Health Checks:**
   ```python
   def before_send_transaction(event, hint):
       if event.get('request', {}).get('url', '').endswith('/health'):
           return None
       return event
   
   sentry_sdk.init(
       before_send_transaction=before_send_transaction,
       ...
   )
   ```

4. **Monitora Quota:**
   - Controlla usage su https://sentry.io/settings/fabriziosalmi/subscription/
   - Verifica se stai raggiungendo i limiti del piano gratuito
