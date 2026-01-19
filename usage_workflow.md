---
description: How to use MacOpenworker
---
# MacOpenworker Usage

## 1. Setup
Ensure you have the environment variables set (OPENROUTER_API_KEY).
Run the installation:
```bash
uv sync
```

## 2. Running the CLI
Start the interactive session:
```bash
uv run python -m openworker.cli start
```
Or if installed as a binary (after `uv pip install -e .`):
```bash
macopenworker start
```

## 3. Interactive Commands
Once inside the shell:
- **Chat**: Just type your request.
- **Index Files**: `> Please scan the ./data folder`
- **RAG Search**: `> What does the report say about revenue?`
- **Write Report**: `> Create a summary file at ./summary.md`
- **Exit**: Type `exit` or `quit`.

## 4. Skills (Coming Soon)
- `/analyze`: Will trigger the multi-step analysis workflow.
