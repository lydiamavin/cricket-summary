# Cricket Comic Strip Generator - Agent Guidelines

## Setup
- **Environment**: Copy `.env.example` to `.env` and add your API keys
- **Virtual Environment**: `source venv/bin/activate` (dependencies already installed)

## Commands
- **Run app**: `streamlit run app.py`
- **Generate comic**: `python src/main.py tests/sample.json`
- **Test single function**: `python -c "from src.main import load_input; print(load_input('tests/sample.json'))"`
- **Lint**: `python -m flake8 src/ app.py` (install flake8 first)
- **Format**: `python -m black src/ app.py` (install black first)

## Code Style
- **Imports**: Standard library first, then third-party, then local. One import per line.
- **Naming**: snake_case for functions/variables, PascalCase for classes (none present).
- **Error handling**: Use ValueError for invalid inputs, check required fields early.
- **Strings**: Use f-strings for formatting, double quotes for consistency.
- **Environment**: Load .env with python-dotenv, use os.getenv() for API keys.
- **Generators**: Set GENERATOR env var to 'openai', 'grok', 'piapi', 'gemini', or 'nano-banana'.
- **API Integration**: Direct API calls to respective services, PiAPI for cloud-hosted models.
- **Types**: No explicit typing required, but validate data structures.
- **Docstrings**: Use for public functions, especially CLI tools.
- **Security**: Never log or expose API keys, validate all inputs.