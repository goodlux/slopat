# Getting Started with slop.at v0.0.1

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/rob/repos/slopat
uv sync
```

### 2. Start the Web Server

```bash
uv run slopat server
```

The server will start on `http://0.0.0.0:8000`

### 3. Test with a Simple Slop

```bash
curl -X POST http://localhost:8000/slop \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Hello World\n\nThis is my first **slop** using GLiNER for concept extraction!"}'
```

You'll get back a response like:
```json
{
  "success": true,
  "hash": "slop-a3f2b9c1",
  "url": "/slop-a3f2b9c1",
  "title": "Hello World",
  "concepts_count": 3,
  "message": "Slop successfully processed and stored!"
}
```

### 4. View Your Slop

Open http://localhost:8000/slop-a3f2b9c1 in your browser to see the beautiful semantic HTML!

Or visit http://localhost:8000/ to see the index of all slops.

## MCP Server Integration (Claude Desktop)

### 1. Add to Claude Desktop Config

Edit `~/.claude.json` and add:

```json
{
  "mcpServers": {
    "slopat": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/rob/repos/slopat",
        "run",
        "python",
        "-m",
        "slopat.server.mcp_server"
      ]
    }
  }
}
```

### 2. Restart Claude Desktop

The MCP server will appear in Claude Desktop with these tools:
- `submit_slop` - Submit markdown and get back a semantic HTML page
- `list_slops` - List all published slops
- `get_slop_stats` - Get statistics about your slop.at instance

### 3. Use from Claude Desktop

```
Can you submit this to slop.at?

# My Research Notes

Today I learned about **distributed consensus algorithms** like Raft and Paxos.
The CAP theorem states that you can only have 2 of 3: Consistency, Availability,
and Partition tolerance.
```

Claude will extract concepts like:
- `distributed consensus algorithms` (computer_science_concept)
- `Raft` (algorithm)
- `Paxos` (algorithm)
- `CAP theorem` (mathematical_theorem)

And return a beautiful color-coded HTML page!

## Architecture

```
Markdown Input
    ↓
GLiNER NER (concept extraction)
    ↓
Topic Classification (auto-gleaned!)
    ↓
Oxigraph Storage (RDF triples)
    ↓
Color-Coded HTML Generation
    ↓
Random Hash URL (e.g., /slop-a3f2b9c1)
```

## Files Generated

All slops are stored in `~/.slopat/slops/` as static HTML files.

## Development

### Run with Auto-Reload

```bash
uv run slopat server --reload
```

### Process a Markdown File Directly

```bash
uv run slopat process my_notes.md
```

### Get Statistics

```bash
uv run slopat stats
```

## Color Coding

- 🔵 **Computer Science** (Blue) - algorithms, data structures, programming
- 🟣 **Mathematics** (Purple) - theorems, proofs, equations
- 🟢 **Social Science** (Green) - research methods, psychology
- 🟡 **Philosophy** (Amber) - concepts, ethics, logic
- 🔴 **People** (Red) - authors, researchers
- ⚪ **Organizations** (Gray) - institutions, companies

## What's Next?

- Phase 2: GitHub integration for storage
- Phase 3: Semantic search and discovery
- Phase 4: Web-based editor
- Future: Federation!

---

**SLOP first, optimize later!** 🐐
