# Quick Setup with uv

## Install uv (if you don't have it)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

## Setup slop.at

```bash
# Clone and enter directory
git clone <your-repo-url>
cd slopat

# Install all dependencies (much faster than pip!)
uv sync

# Run the test
uv run python test_pipeline.py

# Try the CLI
uv run slopat --help
```

## Available Commands

```bash
# Process a file
uv run slopat process data/sample_conversation.txt

# Process a directory  
uv run slopat process data/

# Show statistics
uv run slopat stats

# Find related content
uv run slopat related "Raft"
```

## Development Commands

```bash
# Install with dev dependencies
uv sync --group dev

# Run tests (when we add them)
uv run pytest

# Format code
uv run black slopat/
uv run isort slopat/

# Type checking
uv run mypy slopat/
```

## Why uv?

- **10-100x faster** than pip for dependency resolution
- **Built-in virtual environment** management
- **Lockfile support** for reproducible builds  
- **Compatible with pip** and requirements.txt
- **Single binary** - no Python required to install

Perfect for the fast iteration you need when building slop.at! 🚀
