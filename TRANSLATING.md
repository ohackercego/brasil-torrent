# Translation Guide

Thank you for helping translate Brasil Torrent! The interface currently supports:

- **Português (Brasil)** — `pt-BR` (default)
- **English (US)** — `en-US`

## How Translations Work

All user-visible strings are stored in JSON files inside `client/languages/`:

```
client/languages/
├── pt-BR.json
├── en-US.json
```

The application loads strings using `i18n.t("key")`. The key in the JSON file maps to the translated text.

## Adding a New Language

1. Copy `client/languages/en-US.json` to `client/languages/{locale}.json`
2. Translate all values (keep the keys unchanged)
3. Register the language in `client/core/i18n.py`:

```python
LANGUAGE_NAMES = {
    "en-US": "English (US)",
    "pt-BR": "Português (Brasil)",
    "{locale}": "{Language Name}",
}
```

4. Submit a pull request with the new file and the i18n.py update.

## Translation Rules

- **Do not** change the JSON keys — they are used as identifiers in the code
- **Do not** remove any entries — missing keys will show as `key_name`
- Keep the JSON structure identical
- Use proper Unicode encoding (UTF-8)
- Test with the app: `python client/main.py`

## Updating an Existing Language

If you add a new feature that introduces UI strings, always:

1. Add the key-value pair to **both** existing language files
2. Use the English value as the key name convention (snake_case)
3. Follow the existing style and tone

## Example

```json
{
  "add_torrent": "Add Torrent",
  "torrent_name": "Name"
}
```

Becomes:

```json
{
  "add_torrent": "Adicionar Torrent",
  "torrent_name": "Nome"
}
```

## Testing

After updating translations, run the tests to make sure nothing is broken:

```bash
pytest client/tests/test_i18n.py -v
```
