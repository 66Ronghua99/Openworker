# Openworker

A local AI assistant powered by MCP (Model Context Protocol) with RAG capabilities.

## Features

- **Interactive CLI** - Chat with an AI assistant that can access your local files
- **RAG (Retrieval Augmented Generation)** - Index and search your documents
- **MCP Integration** - Extensible tool system via Model Context Protocol
- **Multi-format Support** - Read PDF, DOCX, Excel, and text files
- **Hybrid Search** - Combines vector search + BM25 with cross-encoder reranking

## Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

### Quick Install

```bash
# Clone the repository
git clone https://github.com/66Ronghua99/MacOpenworker.git
cd MacOpenworker

# Install globally
uv tool install .

# Run from anywhere
openworker
```

### Development Mode

```bash
cd MacOpenworker
uv sync
uv run python -m openworker.cli
```

## Configuration

All configuration is stored in `~/.openworker/`:

| File                | Purpose                              |
| ------------------- | ------------------------------------ |
| `mcp_config.json` | MCP server configurations            |
| `.env`            | API keys (auto-created on first run) |
| `chroma/`         | Vector database for RAG              |
| `openworker.db`   | SQLite database for state            |

### API Key Setup

On first run, you'll be prompted to enter your OpenRouter API key:

```
No API key found. Let's set one up.
Get your API key from: https://openrouter.ai/keys
Enter your OpenRouter API key: sk-or-...
```

Or manually create `~/.openworker/.env`:

```env
OPENROUTER_API_KEY=sk-or-your-key-here
```

## Usage

### Basic Commands

```bash
# Start the assistant
openworker

# In the interactive prompt:
> Hello, what can you do?
```

### Folder Management

```bash
\add /path/to/folder    # Add folder to allowed paths
\rm /path/to/folder     # Remove folder
\folders                # List active folders
```

### Available Tools

| Tool                     | Description                       |
| ------------------------ | --------------------------------- |
| `read_file`            | Read content from local files     |
| `list_files`           | List files in a directory         |
| `write_file`           | Write content to a file           |
| `index_folder`         | Index a folder for RAG search     |
| `search_knowledge`     | Search the indexed knowledge base |
| `reset_knowledge_base` | Clear the RAG index               |

## Architecture

```
openworker/
├── cli.py          # Interactive CLI entry point
├── client.py       # ChatSession with LLM
├── server.py       # MCP server with tools
├── config.py       # Global configuration paths
├── state.py        # SQLite state management
├── core/
│   └── llm.py      # LLM client abstraction
├── rag/
│   ├── store.py    # RAG store (ChromaDB + BM25)
│   ├── splitters.py # Text chunking
│   └── security.py # Path access control
├── tools/
│   └── executor.py # Tool execution with confirmation
└── utils/
    └── readers.py  # File format readers
```

## Environment Variables

| Variable               | Description                 | Default           |
| ---------------------- | --------------------------- | ----------------- |
| `OPENROUTER_API_KEY` | OpenRouter API key          | Required          |
| `OPENAI_API_KEY`     | Alternative: OpenAI API key | -                 |
| `OPENWORKER_HOME`    | Custom config directory     | `~/.openworker` |

## Roadmap

- [ ] **Skills System** - Extensible skill modules for specialized tasks
- [ ] **Browser Extension Control** - Integrate with browser extensions for web automation
- [ ] **Desktop RPA** - Native desktop automation (click, type, screenshot)
- [ ] **Remote MCP Support** - Connect to remote MCP servers via SSE/WebSocket
- [ ] **Multi-agent Orchestration** - Coordinate multiple specialized agents
- [ ] **Model Support** - Support various model selection

## License

MIT
