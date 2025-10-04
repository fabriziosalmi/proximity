# PROXIMITY - IMMEDIATE ACTION CHECKLIST
**Generated:** October 4, 2025  
**Purpose:** Step-by-step guide for next 48 hours  
**Priority:** 🔴 CRITICAL - Do these before anything else

---

## ⏱️ HOUR 1: E2E Test Setup

### Step 1: Install E2E Dependencies
```bash
cd /Users/fab/GitHub/proximity/e2e_tests
pip install -r requirements.txt
```

**Expected Output:**
- pytest-playwright==0.4.4+ installed
- Other dependencies installed
- No errors

**If fails:** Check Python version (need 3.8+)

---

### Step 2: Install Playwright Browsers
```bash
playwright install chromium
```

**Expected Output:**
- Chromium browser downloaded (~150MB)
- Installation complete message

**Storage Note:** Requires ~200MB disk space

---

### Step 3: Initial E2E Test Run
```bash
pytest -v --headed --slowmo=500
```

**Flags Explained:**
- `-v` = Verbose output (see test names)
- `--headed` = Show browser window (see what's happening)
- `--slowmo=500` = Slow down by 500ms (easier to watch)

**Expected Outcome:**
- Some tests will pass ✅
- Some tests will fail ❌ (this is EXPECTED)

---

### Step 4: Capture Results
Create file: `e2e_tests/INITIAL_RUN_RESULTS.md`

```markdown
# E2E Tests - Initial Run Results
Date: [TODAY]

## Summary
- Total: 57 tests
- Passed: X
- Failed: Y
- Skipped: 3

## Failures by Category

### URL/Port Issues
- test_xxx: Expected path-based, got port-based
- test_yyy: ...

### Selector Issues
- test_aaa: Element not found
- test_bbb: ...

### Timing Issues
- test_ccc: Timeout waiting for element
- test_ddd: ...

### Logic Issues
- test_eee: Assertion failed
- test_fff: ...

## Screenshots
[Attach failed test screenshots from test-results/]
```

**Location:** Screenshots auto-saved to `test-results/` folder

---

## 🔍 HOUR 2-3: Failure Analysis

### Analyze Each Failure

For EACH failing test, document:

1. **Test Name:** `test_xxx`
2. **Error Type:** URL mismatch / Selector not found / Timeout / Assertion
3. **Error Message:** Copy full error from terminal
4. **Screenshot:** Note filename in test-results/
5. **Root Cause:** Best guess (port vs path? wrong selector? real bug?)
6. **Fix Estimate:** Easy (15min) / Medium (2hr) / Hard (1 day)
7. **Priority:** P0 (blocker) / P1 (high) / P2 (medium)

**Template:**
```yaml
test_navigate_all_views:
  error_type: "Selector not found"
  message: "Timeout 30000ms exceeded waiting for selector..."
  screenshot: "test_navigate_all_views-retry1-chromium-1696416000.png"
  root_cause: "App cards using new port-based URLs, selector expects path"
  fix_estimate: "Medium (2hr)"
  priority: "P0"
  fix_plan: |
    1. Update app.js line 234 to use port-based URLs
    2. Update selector in test to match new DOM structure
```

---

### Categorize Failures

**URL/Port Mismatches:**
- Frontend still using path-based URLs
- **Fix:** Update app.js to use `http://ip:port` format
- **Priority:** P0
- **Estimated Time:** 4-6 hours

**Selector Issues:**
- DOM structure changed during refactoring
- **Fix:** Update selectors in test files or Page Objects
- **Priority:** P1
- **Estimated Time:** 2-4 hours

**Timing Issues:**
- Race conditions, slow loading
- **Fix:** Add explicit waits, increase timeouts
- **Priority:** P1
- **Estimated Time:** 1-2 hours

**Real Bugs:**
- Functionality actually broken
- **Fix:** Debug and fix backend/frontend code
- **Priority:** P0
- **Estimated Time:** Unknown (investigate first)

---

## 📋 HOUR 4: Create Fix Plan

### Priority Matrix

**P0 - Must Fix Today:**
1. [ ] Fix #1: [description]
   - Owner: [name]
   - Time: [estimate]
   - Blocker: [yes/no]

2. [ ] Fix #2: [description]
   ...

**P1 - Must Fix This Week:**
1. [ ] Fix #5: [description]
2. [ ] Fix #6: [description]

**P2 - Can Defer:**
1. [ ] Fix #10: [description]

---

### Team Assignment

**Backend Dev:**
- [ ] Fix API endpoint issues
- [ ] Fix URL generation in app_service.py
- [ ] Fix any backend bugs discovered

**Frontend Dev:**
- [ ] Fix URL format in app.js
- [ ] Update selectors
- [ ] Fix timing issues

**QA:**
- [ ] Document all failures
- [ ] Re-test after each fix
- [ ] Maintain test status dashboard

---

## 🚀 HOURS 5-8: Start Fixing (Day 1 afternoon)

### Fix Process (Per Test)

1. **Pick highest priority failing test**
2. **Reproduce locally:** `pytest -v test_file.py::test_name --headed`
3. **Debug:**
   - Add print statements
   - Check browser console (F12)
   - Inspect DOM elements
4. **Fix code** (app.js, backend, or test file)
5. **Re-run test:** Verify it passes
6. **Run related tests:** Ensure no regressions
7. **Commit:** `git commit -m "Fix: test_name - issue description"`
8. **Update checklist:** Mark as ✅

---

### Quick Wins First

**Example Easy Fixes:**

#### Fix: Port-based URL in app.js
```javascript
// OLD (line ~234)
const appUrl = `https://domain.com/${appName}/`;

// NEW
const appUrl = `http://${applianceIp}:${app.public_port}/`;
```

#### Fix: Selector for port-based URL
```python
# test file
# OLD
page.click(f"text={app_name} >> ..//*[@href='/{app_name}/']")

# NEW  
page.click(f"text={app_name} >> ..//*[@href*=':{public_port}/']")
```

---

## 📊 HOUR 24: Day 1 End Status

### Status Report Template

```markdown
# E2E Tests - Day 1 Status
Date: [TODAY END]

## Progress
- Tests Fixed: X/Y
- Tests Passing: A/57 (B%)
- Tests Remaining: C

## Fixes Completed Today
1. ✅ test_xxx - Fixed port-based URLs
2. ✅ test_yyy - Updated selector
3. ✅ test_zzz - Increased timeout

## Blockers
- [ ] Issue #1: Need backend API change (waiting for dev)
- [ ] Issue #2: Canvas feature behavior unclear

## Tomorrow's Plan
1. Fix remaining P0 issues (3 tests)
2. Start P1 issues (8 tests)
3. Re-run full suite

## Help Needed
- Backend dev: Fix API endpoint X
- Clarification: How should Canvas feature behave when...?
```

---

## 📊 HOUR 48: Day 2 End - Final Status

### Target Metrics
- [ ] 50+ tests passing (>90%)
- [ ] All P0 issues resolved
- [ ] Test results documented
- [ ] Fix plan for remaining failures
- [ ] Next steps clear

---

## 🎯 Success Criteria

**After 48 hours, you should have:**

✅ E2E tests running  
✅ Clear understanding of all failures  
✅ >50% tests passing (worst case)  
✅ >90% tests passing (best case)  
✅ Documented fix plan for remaining issues  
✅ Team aligned on priorities  

**If NOT achieved:**
- Escalate blockers
- Request additional resources
- Re-estimate timeline

---

## 🆘 Troubleshooting

### Issue: playwright install fails
```bash
# Try with sudo (macOS/Linux)
sudo playwright install chromium

# Or specify path
PLAYWRIGHT_BROWSERS_PATH=$HOME/.playwright playwright install chromium
```

### Issue: Tests hang/freeze
```bash
# Run with timeout
pytest -v --timeout=60

# Or kill stuck processes
pkill -f chromium
```

### Issue: "Module not found" errors
```bash
# Ensure backend in path
export PYTHONPATH=/Users/fab/GitHub/proximity:$PYTHONPATH

# Or install in editable mode
pip install -e /Users/fab/GitHub/proximity/backend
```

### Issue: Database errors
```bash
# Clean test database
rm -f /Users/fab/GitHub/proximity/proximity.db
python backend/main.py  # Recreates DB
```

---

## 📞 Escalation Path

**If stuck for >2 hours on any issue:**
1. Document the blocker in detail
2. Post in team channel with:
   - What you tried
   - Error messages
   - Screenshots
3. Tag: @senior-dev or @tech-lead
4. Move to next priority item while waiting

---

## 📝 Daily Checklist

### Morning (Day 1)
- [ ] Install E2E dependencies
- [ ] Run initial test suite
- [ ] Document all failures
- [ ] Create priority matrix

### Afternoon (Day 1)
- [ ] Fix P0 issues (3-5 tests)
- [ ] Fix quick wins (5-10 tests)
- [ ] Document progress
- [ ] Create Day 2 plan

### Morning (Day 2)
- [ ] Review overnight feedback
- [ ] Continue P0 fixes
- [ ] Start P1 fixes
- [ ] Re-run full suite every 2 hours

### Afternoon (Day 2)
- [ ] Complete remaining P1 fixes
- [ ] Full regression test
- [ ] Document final status
- [ ] Plan Week 2 work

---

**START NOW:** Begin with Hour 1, Step 1 ⬆️

---

*Keep this document updated as you progress*  
*Mark items ✅ as completed*  
*Add notes/learnings as you go*
