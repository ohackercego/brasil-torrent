# Contributing to Brasil Torrent

Thank you for considering contributing to Brasil Torrent! We welcome contributions of all kinds, including bug reports, feature requests, documentation improvements, and code changes.

## Code of Conduct

Please note that this project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.

## How to Contribute

### Reporting Bugs

- Check the [existing issues](https://github.com/azurejoga/brasil-torrent/issues) before creating a new one
- Use a clear and descriptive title
- Include steps to reproduce the bug
- Describe the expected behavior and what actually happened
- Include logs from `log.txt` or `data/brasil_torrent.log`
- Mention your screen reader and version (if reporting an accessibility issue)

### Suggesting Features

- Open a [feature request issue](https://github.com/azurejoga/brasil-torrent/issues/new)
- Explain the use case and why it would be valuable
- Keep accessibility in mind — features should work for all users

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes, keeping the code style consistent
4. Run the tests: `pytest client/tests/`
5. Write or update tests as needed
6. Commit with a clear message describing what and why
7. Push to your fork and open a pull request

## Development Setup

```bash
git clone https://github.com/azurejoga/brasil-torrent.git
cd brasil-torrent
pip install -r requirements.txt
python client/main.py
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use descriptive variable names (Portuguese or English, but be consistent)
- Write docstrings for public methods (PEP 257 style)
- Keep functions focused and small
- All user-visible strings should go through `i18n.t()`

## Accessibility Guidelines

When contributing features, keep these principles in mind:

- **Every control needs a label** — Use `SetLabel()` or `SetAccessible()` 
- **Use keyboard shortcuts** — Map all actions to keys
- **Announce changes** — Status changes, progress updates, and errors should be spoken
- **Don't rely on visuals** — Color, icons, and positioning are secondary to text and focus
- **Test with a screen reader** — Run the app with NVDA or Narrator to verify

## Testing

```bash
# Run all tests
pytest client/tests/

# Run specific test file
pytest client/tests/test_torrent_entry.py

# Run with verbose output
pytest client/tests/ -v
```

We aim for at least 90% test coverage. New features should include tests.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
