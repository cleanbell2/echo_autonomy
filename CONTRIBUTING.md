# Contributing to Echo Autonomy

Thank you for your interest in contributing to Echo Autonomy!

## Quick Start
```bash
# 1. Fork and clone
git clone https://github.com/[username]/echo_autonomy.git
cd echo_autonomy

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
pytest -v
```

## Development Workflow

1. **Create a branch**
```bash
   git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Test your changes**
```bash
   pytest -v --cov
```

4. **Commit**
```bash
   git commit -m "feat: Add your feature"
```

5. **Push and create PR**
```bash
   git push origin feature/your-feature-name
```

## Code Standards

- **Python 3.13+** required
- **Type hints** for all functions
- **100% test coverage** for new code
- **PEP 8** style guide
- **Docstrings** for public APIs

## Commit Message Format
```
<type>: <subject>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- style: Formatting
- chore: Maintenance
```

## Testing
```bash
# Run all tests
pytest -v

# With coverage
pytest -v --cov=bcdsi --cov=q_quantum

# Specific test file
pytest test_bcdsi.py -v

# Production mode
BCDSI_TEST_MODE=false pytest -v
```

## Code Review Process

1. All PRs require tests
2. Tests must pass (53/53 minimum)
3. Code review by maintainer
4. Merge after approval

## Questions?

- Open an issue for bugs
- Start a discussion for features
- Check existing issues first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
