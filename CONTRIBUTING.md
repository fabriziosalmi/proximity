# Contributing to Proximity

We welcome contributions to Proximity! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

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

## 🏗️ Development Setup

### Backend Development

1. **Set up Python environment**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt  # When available
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Proxmox details
   ```

4. **Run the development server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8765
   ```

### Testing

Run tests before submitting your changes:

```bash
# Backend tests
cd backend
pytest

# Code formatting
black .
isort .

# Linting
flake8 .
mypy .
```

## 📝 Coding Standards

### Python Code Style

- **PEP 8**: Follow Python PEP 8 style guide
- **Type Hints**: All functions must have type hints
- **Docstrings**: Use Google-style docstrings
- **Async/Await**: Use async/await for all I/O operations
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
- **Dependency Injection**: Use FastAPI's dependency injection system
- **Single Responsibility**: Each class/function should have one responsibility
- **Error Handling**: Graceful error handling with proper logging

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected vs actual behavior**
4. **Environment details** (Proxmox version, Python version, etc.)
5. **Log files** if relevant

## 💡 Feature Requests

For feature requests:

1. **Check existing issues** to avoid duplicates
2. **Describe the use case** clearly
3. **Explain the benefit** to users
4. **Consider implementation complexity**

## 🔄 Pull Request Process

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

## 📋 Development Workflow

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

## 🏷️ Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

## 📚 Documentation

- **API documentation**: Automatically generated from code
- **User documentation**: Keep README.md updated
- **Code comments**: Document complex logic
- **Architecture decisions**: Document in ADR format

## 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Provide constructive feedback**
- **Follow the code of conduct**

## 🔍 Code Review Guidelines

### For Authors

- **Self-review** your code before submitting
- **Write clear descriptions** of changes
- **Respond promptly** to feedback
- **Make requested changes** or discuss concerns

### For Reviewers

- **Be constructive** and specific
- **Focus on code quality** and maintainability
- **Check for security issues**
- **Verify tests pass**

## 🏆 Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **Hall of Fame** for major contributors

## 📞 Getting Help

If you need help:

1. **Check the documentation**
2. **Search existing issues**
3. **Ask in discussions**
4. **Join our Discord** (coming soon)

## 🚦 Project Status

Current development focus:

- **Phase 1**: Core platform (Complete ✅)
- **Phase 2**: Web interface (In Progress 🚧)
- **Phase 3**: Advanced features (Planned 📋)

Thank you for contributing to Proximity! 🎉