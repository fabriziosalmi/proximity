# Pre-commit Hooks Quick Start Guide

## What You Get

Automated quality gates that run **before every commit**:

- ✅ Code formatting (Black, Ruff)
- ✅ Syntax validation (YAML, JSON)
- ✅ Whitespace cleanup
- ✅ Backend tests (optional - activate when ready)
- ✅ E2E tests (optional - activate when ready)

## Installation (5 Minutes)

### Step 1: Install pre-commit

```bash
# At repository root
pip install -r requirements.txt
```

### Step 2: Install Git hooks

```bash
# One-time command - installs hooks into .git/hooks/
pre-commit install
```

### Step 3: Test the installation

```bash
# Run all active hooks on all files
pre-commit run --all-files
```

✅ **Done!** Hooks will now run automatically on every commit.

## What Happens Now?

### Every time you commit:

```bash
git add .
git commit -m "feat: Add new feature"
```

**Pre-commit will automatically:**

1. Check YAML/JSON syntax
2. Format Python code with Black
3. Lint Python code with Ruff
4. Fix whitespace issues
5. *(If activated)* Run backend tests
6. *(If activated)* Run E2E tests

**If everything passes:** ✅ Commit succeeds

**If anything fails:** ❌ Commit blocked, you fix the issues and try again

## Common Commands

```bash
# Run hooks manually (without committing)
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks for trivial commits (use sparingly!)
git commit -m "docs: Fix typo" --no-verify

# Update hook versions
pre-commit autoupdate

# Clean hook cache
pre-commit clean

# Uninstall hooks
pre-commit uninstall
```

## Gradual Activation

### Phase 1: Code Quality (✅ ACTIVE NOW)

Already running! These hooks are fast (~2-5 seconds) and auto-fix most issues.

### Phase 2: Backend Tests (Activate When Ready)

**When to activate:** Once `pytest tests/` passes 100% reliably

**How to activate:**

1. Verify tests pass:
   ```bash
   pytest tests/ -v
   ```

2. Edit `.pre-commit-config.yaml` at repository root

3. Find this section and **uncomment it** (remove the `#` symbols):
   ```yaml
   # - repo: local
   #   hooks:
   #     - id: pytest-backend
   #       name: 🔒 Backend Test Guardian
   #       ...
   ```

4. Test the hook:
   ```bash
   pre-commit run pytest-backend --all-files
   ```

5. If all tests pass, commit the change:
   ```bash
   git add .pre-commit-config.yaml
   git commit -m "chore: Activate backend test guardian"
   ```

### Phase 3: E2E Tests (Activate When Ready)

**When to activate:** Once `pytest e2e_tests/` passes 100% reliably

**How to activate:** Same process as Phase 2, but uncomment the `pytest-e2e` section

**⚠️ Note:** E2E tests can take 5-10 minutes. Consider using `--no-verify` for minor commits during active development.

## Performance Tips

### Fast Development Workflow

```bash
# Commit frequently without E2E tests
git commit -m "WIP: Feature development"

# Before pushing, run full test suite manually
./run_all_tests.sh

# Push with confidence
git push origin feature-branch
```

### Skip Slow Tests Temporarily

For minor commits during active development:

```bash
# Skip ALL hooks (including E2E tests)
git commit -m "refactor: Rename variable" --no-verify
```

**Remember:** CI/CD will still run all tests!

## Troubleshooting

### Hook fails with ModuleNotFoundError

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or your venv path

# Reinstall dependencies
pip install -r backend/requirements.txt
pip install -r tests/requirements.txt
pip install -r e2e_tests/requirements.txt
```

### E2E tests fail - backend not running

```bash
# Option 1: Start backend manually in another terminal
cd backend
python main.py

# Option 2: Use unified test runner (auto-starts backend)
./run_all_tests.sh --e2e-only
```

### Black/Ruff makes unwanted changes

```bash
# View changes before committing
git diff

# If you disagree with auto-formatting:
# 1. Configure Black/Ruff in pyproject.toml
# 2. Or add specific files to exclude in .pre-commit-config.yaml
```

### Hook is too slow

```bash
# Temporarily skip for this commit
git commit -m "message" --no-verify

# For permanent solution:
# 1. Move slow hooks to pre-push instead of pre-commit
# 2. Or make hooks run only when relevant files change
```

## Configuration Files

All hook configuration is in `.pre-commit-config.yaml` at repository root.

**Key sections:**

- `repos`: List of hook repositories (local or remote)
- `hooks`: Individual hook definitions
- `id`: Unique hook identifier
- `entry`: Command to execute
- `types`: File types that trigger the hook
- `always_run`: Run even if no matching files changed

## Best Practices

✅ **DO:**
- Run `pre-commit run --all-files` after pulling changes
- Fix issues immediately when hooks fail
- Let hooks run for significant code changes
- Use hooks to maintain code quality

❌ **DON'T:**
- Use `--no-verify` to bypass failing tests
- Disable hooks permanently without team discussion
- Commit broken code assuming "CI will catch it"

## Why Pre-commit Hooks?

### Benefits

1. **Catch issues early** - Before they reach remote repository
2. **Automated formatting** - No more style debates
3. **Faster CI/CD** - Fewer pipeline failures
4. **Better code quality** - Consistent, clean codebase
5. **Save time** - Automated checks are faster than manual review

### When to Skip

Only use `--no-verify` for:
- Documentation typo fixes
- Comment changes
- README updates
- Minor whitespace cleanup

**Never skip for:**
- New features
- Bug fixes
- Refactoring
- Dependency changes

## Getting Help

- **Pre-commit docs**: https://pre-commit.com/
- **Project docs**: See `CONTRIBUTING.md` and `docs/development.md`
- **Issues**: Check `.pre-commit-config.yaml` comments for troubleshooting

---

**Happy coding! 🚀 Your commits are now protected by automated quality gates.**
