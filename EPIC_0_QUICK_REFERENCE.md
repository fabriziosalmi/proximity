# 🎯 EPIC 0 Quick Reference Card

**Mission:** Achieve 150% confidence in codebase before adding new features

---

## 📊 Current Baseline

```
Backend Tests:  259 tests collected ⚠️  (needs pass verification)
E2E Tests:      ~120 tests ⚠️  (needs count verification)
Integration:    ❌ Not implemented
```

---

## ⚡ Quick Commands

### Backend Tests
```bash
# Run all backend tests
cd tests && pytest -v --tb=short

# Run clone/config tests only
cd tests && pytest test_app_clone_config.py -v

# Check for warnings
cd tests && pytest -W error::RuntimeWarning -v

# Generate coverage report
cd tests && pytest --cov=backend --cov-report=html
```

### E2E Tests
```bash
# Run all E2E tests
cd e2e_tests && pytest -v --tb=short

# Run auth tests only
cd e2e_tests && pytest test_auth_flow.py -v

# Run navigation tests
cd e2e_tests && pytest test_navigation.py -v

# Run core flow test
cd e2e_tests && pytest test_complete_core_flow.py -v
```

### Quick Start Script
```bash
# Show progress dashboard
./epic0_quick_start.sh progress

# Run backend tests
./epic0_quick_start.sh backend

# Check auth fixture stability
./epic0_quick_start.sh stress

# Generate status report
./epic0_quick_start.sh report
```

---

## 🎯 The Four Pillars

### PILLAR 1: Backend Test Perfection
**Goal:** 259/259 tests passing, 0 warnings

**Priority Tasks:**
1. ✅ Fix Clone/Config tests (`test_app_clone_config.py`)
2. ✅ Eliminate RuntimeWarnings (async/await issues)
3. ✅ Achieve 100% pass rate

**Files to Check:**
- `tests/test_app_clone_config.py`
- `tests/conftest.py`
- `backend/services/app_service.py`

### PILLAR 2: E2E Test Reliability
**Goal:** Zero TargetClosedError, stable auth fixture

**Priority Tasks:**
1. ✅ Eliminate TargetClosedError
2. ✅ Strengthen auth fixture (5-layer wait → 7-layer)
3. ✅ Verify navigation stability

**Files to Check:**
- `e2e_tests/conftest.py` (authenticated_page fixture)
- `e2e_tests/test_auth_flow.py`
- `e2e_tests/test_navigation.py`

### PILLAR 3: Critical Flow Coverage
**Goal:** Full lifecycle, backup/restore, update tests

**Priority Tasks:**
1. ✅ Create `test_full_lifecycle.py`
2. ✅ Create `test_backup_restore.py`
3. ✅ Create `test_app_update.py`

**New Files to Create:**
- `e2e_tests/test_full_lifecycle.py`
- `e2e_tests/test_backup_restore.py`
- `e2e_tests/test_app_update.py`

### PILLAR 4: Real Integration Validation
**Goal:** Proxmox integration tests passing

**Priority Tasks:**
1. ✅ Create `tests/integration/test_proxmox_real.py`
2. ✅ Setup test environment (.env.test)
3. ✅ Run against dev Proxmox

**New Files to Create:**
- `tests/integration/test_proxmox_real.py`
- `.env.test` (DO NOT COMMIT)
- `tests/integration/README.md`

---

## 🚀 Execution Phases

### Phase 1: Quick Wins (Days 1-2)
```bash
# Day 1
./epic0_quick_start.sh clone      # Fix clone tests
./epic0_quick_start.sh warnings   # Fix warnings

# Day 2
./epic0_quick_start.sh stress     # Test auth stability
./epic0_quick_start.sh backend    # Verify 100% pass
```

### Phase 2: Core Stability (Days 3-4)
```bash
# Day 3
cd e2e_tests && pytest test_navigation.py -v  # Verify nav
cd e2e_tests && pytest test_auth_flow.py -v   # Verify auth

# Day 4
./epic0_quick_start.sh all  # Full suite + report
```

### Phase 3: Critical Coverage (Days 5-7)
```bash
# Day 5: Implement test_full_lifecycle.py
cd e2e_tests && pytest test_full_lifecycle.py -v

# Day 6: Implement test_backup_restore.py
cd e2e_tests && pytest test_backup_restore.py -v

# Day 7: Implement test_app_update.py
cd e2e_tests && pytest test_app_update.py -v
```

### Phase 4: Real Validation (Days 8-10)
```bash
# Day 8: Setup integration tests
cd tests/integration
pytest test_proxmox_real.py -v -m real_proxmox

# Day 9: Full test marathon
./epic0_quick_start.sh all  # Run 10 times

# Day 10: Documentation
./epic0_quick_start.sh report
# Write completion reports
```

---

## 🔍 Troubleshooting Quick Fixes

### "RuntimeWarning: coroutine was never awaited"
```python
# WRONG ❌
mock.method = AsyncMock(return_value="value")
result = mock.method()

# CORRECT ✅
mock.method = AsyncMock(return_value="value")
result = await mock.method()
```

### "TargetClosedError: Target page closed"
```python
# Add page health check before operations
def safe_click(page, selector):
    if page.is_closed():
        raise RuntimeError("Page is closed!")
    page.click(selector)
```

### "Auth fixture flaky"
```python
# Use all 7 layers of wait:
# 1. Token in storage
# 2. Modal closed
# 3. Dashboard container visible
# 4. Dashboard loaded attribute
# 5. No loading spinners
# 6. App initialized
# 7. API health check
```

### "Test collection failed"
```bash
# Check Python path and imports
cd tests
python -c "import sys; print('\n'.join(sys.path))"

# Verify pytest.ini is correct
cat pytest.ini

# Clear pytest cache
rm -rf .pytest_cache __pycache__
```

---

## 📈 Success Metrics

### PILLAR 1 Complete:
```
✅ 259/259 backend tests passing
✅ 0 RuntimeWarnings
✅ 0 test collection errors
✅ < 60s total execution time
```

### PILLAR 2 Complete:
```
✅ 0 TargetClosedError in 10 runs
✅ 100% auth test pass rate (10 runs)
✅ Navigation tests < 25s total
✅ Zero flaky tests
```

### PILLAR 3 Complete:
```
✅ test_full_lifecycle.py passing
✅ test_backup_restore.py passing
✅ test_app_update.py passing
✅ All critical flows covered
```

### PILLAR 4 Complete:
```
✅ Integration tests implemented
✅ Tests pass against real Proxmox
✅ Cleanup guaranteed
✅ Documentation complete
```

---

## 🎯 Definition of Done

EPIC 0 is complete when:

- [ ] Backend: 259/259 passing, 0 warnings
- [ ] E2E: 100% pass rate on critical flows
- [ ] Reliability: 10 consecutive full runs with 0 failures
- [ ] Integration: Proxmox tests passing
- [ ] Documentation: Complete reports generated
- [ ] Team: Everyone agrees codebase is solid

---

## 📚 Key Documents

1. `EPIC_0_MASTER_PLAN.md` - Full detailed plan (this is your bible)
2. `EPIC_0_QUICK_REFERENCE.md` - This quick reference card
3. `epic0_quick_start.sh` - Automation script
4. `E2E_TEST_STABILIZATION_REPORT.md` - Previous fixes documented

---

## 🆘 Need Help?

### Common Issues:
1. **Tests won't collect**
   - Check pytest.ini
   - Verify Python path
   - Clear cache: `rm -rf .pytest_cache`

2. **Async warnings everywhere**
   - Search for AsyncMock without await
   - Use: `grep -r "AsyncMock" tests/`

3. **E2E tests randomly fail**
   - Check authenticated_page fixture
   - Add more wait layers
   - Use page.is_closed() checks

4. **Integration tests fail**
   - Verify PROXMOX_HOST env var set
   - Check Proxmox credentials
   - Ensure test VMID range is free (9000-9999)

---

## 💪 Daily Routine

### Start of Day:
```bash
./epic0_quick_start.sh progress  # Check status
git pull origin main              # Get latest
```

### During Development:
```bash
# After fixing something
./epic0_quick_start.sh backend   # Quick backend check
./epic0_quick_start.sh e2e       # Quick E2E check
```

### End of Day:
```bash
./epic0_quick_start.sh report    # Generate report
git commit -am "EPIC 0: [description]"
git push
```

---

## 🎉 Celebration Milestones

- 🎊 First 100% backend pass: Buy coffee
- 🎊 Zero TargetClosedError (10 runs): Lunch break
- 🎊 All critical flows passing: Pizza party
- 🎊 EPIC 0 complete: Victory dance! 🕺

---

**Remember:** Stability first, features second! 🚀

---

**Quick Reference Version:** 1.0  
**Last Updated:** October 16, 2025
