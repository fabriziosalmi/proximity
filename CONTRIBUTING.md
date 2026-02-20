# Contributing to Proximity

We welcome contributions to Proximity! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/proximity.git
   cd proximity
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Backend Development

1. **Set up Python environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Proxmox details
   ```

3. **Run the development server**:
   ```bash
   env USE_MOCK_PROXMOX=1 python manage.py runserver
   ```

### Testing

Run tests before submitting your changes:

```bash
# Run backend tests (use pytest, not manage.py test)
cd backend
env USE_MOCK_PROXMOX=1 pytest -v

# Run specific test file
env USE_MOCK_PROXMOX=1 pytest tests/test_models.py

# Run E2E tests (requires backend running)
cd e2e_tests
pytest --browser chromium -v
```

### Pre-commit Hooks

The repository uses pre-commit hooks to maintain code quality.

#### What Are Pre-commit Hooks?

Pre-commit hooks are automated checks that run **before every commit**. They act as quality gates, ensuring:

- ✅ Code is properly formatted (Black, Ruff)
- ✅ No syntax errors in YAML/JSON files
- ✅ No trailing whitespace or mixed line endings
- ✅ **Backend tests pass 100%** (when activated)
- ✅ **E2E tests pass 100%** (when activated)

If any check fails, **the commit is blocked** until you fix the issues.

#### Installation (One-Time Setup)

After cloning the repository and setting up your virtual environment:

```bash
# Install pre-commit framework
pip install -r requirements.txt  # This includes pre-commit

# Install the Git hooks (ONE-TIME command per repository clone)
pre-commit install

# ✅ Done! Hooks will now run automatically on every commit
```

#### What Runs on Every Commit?

**Phase 1: Code Quality (ACTIVE NOW)** ⚡ Fast (~2-5 seconds)

These hooks run immediately and automatically fix most issues:

- **YAML/JSON validation**: Prevents syntax errors in config files
- **Black formatter**: Auto-formats Python code to PEP 8 style
- **Ruff linter**: Catches common Python issues and auto-fixes them
- **Whitespace fixes**: Removes trailing spaces, ensures newlines at end of files
- **Large file detection**: Prevents accidentally committing files >500KB
- **Merge conflict detection**: Catches unresolved conflict markers

**Phase 2: Backend Test Guardian (READY - Uncomment to activate)** 🐍 Medium (~10-30 seconds)

When activated, this hook runs the entire backend pytest suite:

```bash
pytest tests/ --tb=short -q
```

If any backend test fails, **the commit is blocked**. This prevents:
- Broken API endpoints
- Database schema issues
- Authentication/authorization bugs
- Business logic regressions

**Phase 3: E2E Test Guardian (READY - Uncomment to activate)** 🎭 Slow (~5-10 minutes)

When activated, this hook runs the full Playwright E2E suite:

```bash
pytest e2e_tests/ --browser chromium --tb=short -q
```

If any E2E test fails, **the commit is blocked**. This prevents:
- UI regressions
- Broken user workflows
- Integration issues between frontend and backend

#### Running Hooks Manually

You can run all hooks without making a commit:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run all hooks on staged files only
pre-commit run

# Run specific hook
pre-commit run black --all-files
pre-commit run pytest-backend --all-files
```

**Use this after activating new hooks** to ensure everything passes before committing.

#### Skipping Hooks (Use Sparingly!)

For **trivial commits only** (typos in comments, minor doc changes), you can bypass hooks:

```bash
# Skip ALL hooks for this commit
git commit -m "docs: Fix typo in README" --no-verify
```

**⚠️ WARNING: Use --no-verify ONLY for trivial changes!**

- The CI/CD pipeline will still run all tests regardless
- Your PR may be rejected if tests fail in CI
- Use this for minor documentation fixes, not code changes

#### Gradual Activation Strategy

The `.pre-commit-config.yaml` file uses a **phased approach** to activate hooks:

**RIGHT NOW (Phase 1)**: Code quality hooks are ACTIVE
- Run on every commit automatically
- Fix formatting and linting issues
- Very fast, no impact on developer flow

**When Backend Tests Are Stable (Phase 2)**:
1. Ensure `pytest tests/` passes 100%
2. Edit `.pre-commit-config.yaml`
3. Uncomment the `pytest-backend` hook section
4. Run `pre-commit run --all-files`
5. Commit the change

**When E2E Tests Are Stable (Phase 3)**:
1. Ensure `pytest e2e_tests/` passes 100%
2. Edit `.pre-commit-config.yaml`
3. Uncomment the `pytest-e2e` hook section
4. Run `pre-commit run --all-files`
5. Commit the change

#### Troubleshooting

**Hook fails with import errors:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # or your venv path

# Reinstall dependencies
pip install -r backend/requirements.txt
pip install -r tests/requirements.txt
pip install -r e2e_tests/requirements.txt
```

**E2E hook fails - backend not running:**
```bash
# Start backend in another terminal
cd backend
python main.py

# Then retry your commit
```

**Want to update hook versions:**
```bash
pre-commit autoupdate
```

**Want to clean hook cache:**
```bash
pre-commit clean
```

**Want to uninstall hooks:**
```bash
pre-commit uninstall
```

#### Best Practices

1. **Always let hooks run** for significant code changes
2. **Fix issues immediately** - don't try to bypass hooks repeatedly
3. **Use --no-verify sparingly** - only for truly trivial commits
4. **Run hooks manually** after pulling changes: `pre-commit run --all-files`
5. **Keep hooks fast** - if E2E tests are too slow, consider pre-push hooks instead

#### Performance Tips

- **Code quality hooks**: ~2-5 seconds (negligible impact)
- **Backend tests**: ~10-30 seconds (acceptable for most commits)
- **E2E tests**: ~5-10 minutes (consider using `--no-verify` for minor commits)

**For faster commits during active development:**
- Work on a feature branch
- Commit frequently without E2E hooks
- Run full suite (`./run_all_tests.sh`) before pushing to remote
- Let CI/CD validate everything

#### CI/CD Integration

Pre-commit hooks are your **first line of defense**, but remember:

- CI/CD will **always** run the full test suite, regardless of `--no-verify`
- Failed tests in CI will block PR merges
- Hooks save you time by catching issues before pushing

## Coding Standards

### Python Code Style

- **PEP 8**: Follow Python PEP 8 style guide
- **Type Hints**: All functions should have type hints
- **Docstrings**: Use Google-style docstrings
- **Error Handling**: Proper exception handling with custom exceptions

Example:
```python
async def create_lxc(self, node: str, vmid: int, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new LXC container.

    Args:
        node: Proxmox node name
        vmid: Virtual machine ID
        config: Container configuration

    Returns:
        Dict containing task information

    Raises:
        ProxmoxError: If container creation fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        raise ProxmoxError(f"Failed to create LXC {vmid}: {e}")
```

### Architecture Principles

- **Separation of Concerns**: Keep API, business logic, and data layers separate
- **Single Responsibility**: Each class/function should have one responsibility
- **Error Handling**: Graceful error handling with proper logging

## Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected vs actual behavior**
4. **Environment details** (Proxmox version, Python version, etc.)
5. **Log files** if relevant

## Feature Requests

For feature requests:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the benefit** to users
4. **Consider implementation complexity**

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** if applicable
5. **Create descriptive commit messages**

### Commit Message Format

Use conventional commits:

```
type(scope): brief description

Longer description if needed

Closes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

Examples:
```
feat(api): add application scaling endpoints
fix(proxmox): handle connection timeout errors
docs(readme): update installation instructions
```

## Development Workflow

### Feature Development

1. **Create issue** or check existing ones
2. **Create feature branch** from `main`
3. **Implement feature** with tests
4. **Update documentation**
5. **Submit pull request**

### Bug Fixes

1. **Create issue** with reproduction steps
2. **Create bugfix branch**
3. **Fix the bug** with tests
4. **Submit pull request**

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## Documentation

- **API documentation**: Auto-generated from code (Django Ninja)
- **User documentation**: Keep README.md updated
- **Code comments**: Document complex logic

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Follow the code of conduct

## Code Review Guidelines

### For Authors

- Self-review your code before submitting
- Write clear descriptions of changes
- Respond to feedback
- Make requested changes or explain disagreements

### For Reviewers

- Be constructive and specific
- Focus on code quality and maintainability
- Check for security issues
- Verify tests pass

## Getting Help

If you need help:

1. **Check the documentation**
2. **Search existing issues**
3. **Open a new issue** on GitHub

## Project Status

See [STATUS.md](STATUS.md) for the current state of the project, including known gaps and planned work.

Thank you for contributing to Proximity!
