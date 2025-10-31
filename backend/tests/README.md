# Backend Unit Tests

Questa directory contiene i test unitari per il backend di Proximity 2.0.

## 📁 Struttura

```
tests/
├── __init__.py           # Package initialization
├── conftest.py          # Pytest fixtures condivise
├── test_models.py       # Test per i modelli Django
├── test_schemas.py      # Test per gli schemi Pydantic
├── test_services.py     # Test per i servizi business logic
├── test_auth.py         # Test per autenticazione e permessi
└── test_utils.py        # Test per utility e helper functions
```

## 🧪 Tipi di Test

### Test dei Modelli (`test_models.py`)
- Creazione e validazione dei modelli Django
- Relazioni tra modelli (ForeignKey, OneToOne, etc.)
- Proprietà e metodi custom
- Vincoli di unicità e integrità
- Segnali e callback (save, delete, etc.)

### Test degli Schemi (`test_schemas.py`)
- Validazione Pydantic
- Serializzazione/deserializzazione
- Campi obbligatori e opzionali
- Validatori custom
- Trasformazioni dei dati

### Test dei Servizi (`test_services.py`)
- Logica di business
- PortManagerService (allocazione porte)
- CatalogService (gestione catalogo)
- ProxmoxService (interazione con Proxmox)
- Mock di API esterne

### Test di Autenticazione (`test_auth.py`)
- JWT token generation e validazione
- Password hashing
- Permessi e ownership
- Autenticazione API

### Test Utility (`test_utils.py`)
- Helper functions
- Data transformations
- Query optimization
- Error handling
- Request validation

## 🚀 Esecuzione dei Test

### Eseguire tutti i test
```bash
cd backend
pytest tests/
```

### Eseguire un file specifico
```bash
pytest tests/test_models.py
```

### Eseguire una classe specifica
```bash
pytest tests/test_models.py::TestUserModel
```

### Eseguire un test specifico
```bash
pytest tests/test_models.py::TestUserModel::test_create_user
```

### Con output dettagliato
```bash
pytest tests/ -v -s
```

### Con coverage
```bash
pytest tests/ --cov=apps --cov-report=html
```

## 📊 Coverage Report

Per generare un report di copertura del codice:

```bash
# Installa pytest-cov se non è già installato
pip install pytest-cov

# Genera report HTML
pytest tests/ --cov=apps --cov-report=html

# Apri il report
open htmlcov/index.html
```

## 🎯 Best Practices

### 1. Nomenclatura
- File di test: `test_*.py`
- Classi di test: `Test*`
- Metodi di test: `test_*`
- Fixture: nomi descrittivi senza prefisso test

### 2. Struttura dei Test
```python
def test_something(fixture1, fixture2):
    """Test description."""
    # Arrange: Setup
    data = {'key': 'value'}

    # Act: Execute
    result = function_to_test(data)

    # Assert: Verify
    assert result == expected_value
```

### 3. Uso delle Fixture
- Usa fixture per setup comune
- Mantieni le fixture semplici e focalizzate
- Usa `@pytest.fixture(scope='session')` per dati costosi da creare

### 4. Mock delle Dipendenze Esterne
```python
@patch('module.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {'data': 'mocked'}
    result = function_that_uses_api()
    assert result is not None
```

### 5. Test del Database
- Usa `@pytest.mark.django_db` per test che accedono al database
- Il database viene rollback automaticamente dopo ogni test
- Usa fixture per creare dati di test

## 🔧 Configurazione

### pytest.ini
```ini
[pytest]
DJANGO_SETTINGS_MODULE = proximity.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --reuse-db
testpaths = tests
```

### conftest.py
Contiene fixture condivise:
- `test_user`: Utente di test
- `admin_user`: Utente admin
- `proxmox_host`: Host Proxmox di test
- `test_application`: Applicazione di test
- `test_backup`: Backup di test
- `mock_proxmox_api`: Mock dell'API Proxmox

## 📝 Aggiungere Nuovi Test

1. Crea un nuovo file `test_*.py` se necessario
2. Importa le dipendenze necessarie
3. Usa `@pytest.mark.django_db` per test database
4. Scrivi test descrittivi con docstring
5. Usa fixture esistenti quando possibile
6. Mock le dipendenze esterne

Esempio:
```python
import pytest
from apps.myapp.models import MyModel

@pytest.mark.django_db
class TestMyModel:
    """Test MyModel functionality."""

    def test_create_instance(self):
        """Test creating a MyModel instance."""
        instance = MyModel.objects.create(
            name='Test',
            value=42
        )
        assert instance.name == 'Test'
        assert instance.value == 42
```

## 🐛 Debug dei Test

### Eseguire con debugger
```bash
pytest tests/test_models.py --pdb
```

### Stampare output durante i test
```bash
pytest tests/ -s
```

### Vedere solo i test falliti
```bash
pytest tests/ --lf
```

### Vedere tempo di esecuzione
```bash
pytest tests/ --durations=10
```

## 📚 Risorse

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Pytest-Django](https://pytest-django.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## ✅ Checklist Test Coverage

### Modelli
- [ ] Creazione istanze
- [ ] Validazione campi
- [ ] Vincoli unicità
- [ ] Relazioni
- [ ] Proprietà custom
- [ ] Metodi custom
- [ ] Segnali

### API
- [ ] Endpoints esistenti
- [ ] Autenticazione
- [ ] Autorizzazione
- [ ] Validazione input
- [ ] Response format
- [ ] Error handling
- [ ] Status codes

### Servizi
- [ ] Business logic
- [ ] Interazione con modelli
- [ ] Chiamate API esterne (mocked)
- [ ] Error handling
- [ ] Edge cases

### Utility
- [ ] Helper functions
- [ ] Data transformations
- [ ] Validatori
- [ ] Formattatori
