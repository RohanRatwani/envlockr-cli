# Contributing to EnvLockr

Thank you for your interest in contributing to EnvLockr! 🎉

## Quick Start

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/envlockr-cli.git
   cd envlockr-cli
   ```

2. **Install in development mode**
   ```bash
   pip install -e .
   ```

3. **Test your installation**
   ```bash
   envlockr --version
   envlockr --help
   ```

## Development

### Running Tests

```bash
# Run unit tests
python run_tests.py

# Manual testing
envlockr add TEST_KEY
envlockr get TEST_KEY
envlockr list
envlockr delete TEST_KEY
```

### Code Style

- Follow PEP 8 guidelines
- Add comments for complex logic
- Keep functions focused and simple

## Feature Requests

Have an idea? Open an issue with:
- Clear description of the feature
- Use case / problem it solves
- Example usage

## Bug Reports

Found a bug? Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)

## Pull Requests

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push and create a PR

## Questions?

- 💬 [Open a Discussion](https://github.com/RohanRatwani/envlockr-cli/discussions)
- 🐛 [Report an Issue](https://github.com/RohanRatwani/envlockr-cli/issues)

Thank you for contributing! 🙏
