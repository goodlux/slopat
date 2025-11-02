# Claude Instructions for slop.at

## Git Collaboration

When creating commits for this project:
- Always include co-authorship: `Co-Authored-By: spacegoatai <spacegoatai@gmail.com>`
- spacegoatai is my GitHub identity: https://github.com/spacegoatai

## Documentation Standards

All new documentation files must follow this naming convention:

```
YYYY_MM_DD_TITLE_IN_CAPS.md
```

Example:
- `2025_10_30_GLINER_PROCESSING_FLOW.md`
- `2025_10_30_WEB_SERVER_ARCHITECTURE.md`
- `2025_10_30_MCP_INTEGRATION_SPEC.md`

Store all docs in the `docs/` directory.

## Project Context

slop.at is a semantic knowledge platform that:

1. Receives markdown documents via MCP server
2. Processes them through GLiNER for Named Entity Recognition
3. Extracts and categorizes topics automatically (GLEANED, not predefined!)
4. Stores semantic relationships in Oxigraph (RDF graph database)
5. Generates color-coded HTML with **synesthetic highlighting**
6. Posts to random hash URLs at slop.at

## Current Architecture

```
MCP .md input → GLiNER NER → GLEANED topics → Oxigraph storage → Color-coded HTML → Random hash URL
```

## Special Sauce

- **Auto-categorization**: Categories are GLEANED by GLiNER, not predefined
- **Synesthetic colors**: Each topic/domain gets a unique color for visual semantic mapping
- **Graph-first**: All relationships stored in RDF for semantic querying
- **Random URLs**: Each slop gets a unique hash for anonymous sharing
- **MCP-native**: Built to integrate with Claude Desktop and other MCP clients

## Development Philosophy

- Start simple, iterate fast
- SLOP first, optimize later
- Let GLiNER discover structure
- Visual semantics > traditional categorization
- No Pixeltable (that's old news!)
