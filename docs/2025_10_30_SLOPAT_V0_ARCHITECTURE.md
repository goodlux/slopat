# slop.at v0.0.1 Architecture & Vision

**Date:** October 30, 2025  
**Status:** Initial Development Phase  
**Context:** Ideas synthesized from July-October 2025 conversations

## Core Concept

slop.at is a semantic web publishing platform that transforms text into beautiful, semantically-linked web pages with automatic concept extraction and graph-based discovery. Think "gist meets semantic web" - a place where ideas live, connect, and evolve.

## Key Architectural Decisions

### 1. GitHub as Backend Storage

**Anonymous Posts:**
- Stored in shared repository (`slopat/anonymous-slops` or similar)
- Community-owned content
- Public by default

**Personal Posts:**
- Stored in individual user GitHub repos
- User maintains full ownership and control
- Enables portability and data sovereignty

**Benefits:**
- Versioning built-in (git history)
- Permanence and reliability
- Developer-friendly (familiar tools)
- Enables unique social mechanics (forking, PRs for collaboration)
- Free hosting and CDN via GitHub

### 2. Semantic Processing Pipeline

```
Text Input → GLiNER Extraction → Ontology Mapping → RDF Triples → Oxigraph Storage → HTML Generation
```

**Components:**

1. **Document Parser**
   - Markdown-first approach
   - Auto-detect document types (conversations, structured text, plain text)
   - Extract titles and metadata

2. **GLiNER Concept Extraction**
   - Multi-ontology support:
     - Computer Science (algorithms, data structures, programming concepts)
     - Mathematics (theorems, proofs, mathematical objects)
     - Philosophy (philosophical concepts, schools of thought)
     - Social Sciences (theories, methodologies, social phenomena)
   - Domain-agnostic entity recognition
   - Confidence scoring

3. **Ontology Mapping**
   - Convert extracted concepts to RDF triples
   - Map to standard ontologies (schema.org, FOAF, Dublin Core, custom)
   - Maintain semantic relationships

4. **Oxigraph Storage**
   - RDF graph database
   - SPARQL query support
   - Stores relationships between concepts and slops
   - Enables semantic discovery

5. **HTML Generation**
   - Beautiful, clean interface
   - Domain-specific color coding:
     - Purple: People/Authors
     - Blue: Mathematics
     - Green: Science/Technology
     - Gold: Philosophy/Theory
   - Interactive concept highlighting
   - Sidebar navigation showing related slops

### 3. Three-Column Layout

```
┌─────────────────────────────────────────────────────────┐
│                      Header/Nav                          │
├──────────────┬──────────────────────┬───────────────────┤
│   Sidebar    │                      │   Related Slops   │
│   (Left)     │   Main Content       │   (Right)         │
│              │                      │                   │
│  - Concepts  │   [Document Text     │   - Graph-based   │
│  - Metadata  │    with highlighted  │     discovery     │
│  - Tags      │    concepts]         │   - Semantic      │
│              │                      │     links         │
│              │                      │   - Recent slops  │
└──────────────┴──────────────────────┴───────────────────┘
```

## Integration Concepts

### Pixeltable Backend (Alternative/Complement)

- Multimedia processing pipeline
- Handle images, video, audio alongside text
- Stable Pixeltable IDs as reference anchors
- Cross-modal semantic analysis
- Built-in versioning and provenance tracking

**Use case:** When slop.at needs to handle rich media content, not just text

### ASI-ARCH Research Integration

**Vision:** Research papers as living, conversational documents

- slop.at → ASI-ARCH: Feed research discussions as input
- ASI-ARCH → slop.at: Publish evolved research insights
- Create continuous research evolution cycle
- Enable ASI-ARCH instances to discover and build on each other's work
- Distributed research intelligence network

### Federated Model

**Individual slop servers that interconnect:**
- Users run their own instances
- Servers share semantic graphs
- Decentralized knowledge network
- Privacy-preserving discovery
- Nuclear updates for reference integrity

## Technology Stack (v0.0.1)

### Core
- Python 3.10+
- uv for dependency management

### NLP & Semantic
- GLiNER (concept extraction)
- Oxigraph (RDF graph database)
- SPARQL for queries

### Web
- Static HTML generation (initially)
- Consider: Tiptap/Milkdown for WYSIWYG markdown editor
- Tailwind CSS for styling

### Storage & Publishing
- GitHub API for repo management
- Git for versioning
- GitHub Pages for hosting (optional)

## Development Roadmap

### Phase 1: Core Pipeline (v0.0.1)
- [ ] Markdown parser
- [ ] GLiNER integration
- [ ] Basic ontology mapping
- [ ] Oxigraph storage
- [ ] HTML generation with highlighting
- [ ] Local file system testing

### Phase 2: GitHub Integration (v0.0.2)
- [ ] GitHub OAuth
- [ ] Repo creation/management
- [ ] Commit and push slops
- [ ] Read from GitHub repos
- [ ] Basic social features (stars, forks)

### Phase 3: Discovery & Navigation (v0.0.3)
- [ ] Semantic search
- [ ] Graph visualization
- [ ] Related slops algorithm
- [ ] Topic clustering
- [ ] Timeline views

### Phase 4: Publishing Interface (v0.1.0)
- [ ] Web-based editor
- [ ] Real-time concept highlighting
- [ ] Draft management
- [ ] Collaborative editing (via PRs)

### Future: Federation & Scale
- [ ] Federated server protocol
- [ ] Pixeltable multimedia backend
- [ ] ASI-ARCH integration
- [ ] Mobile apps
- [ ] Browser extensions

## Key Design Principles

1. **Data Ownership:** Users own their content (via GitHub repos)
2. **Semantic First:** Everything is connected through meaning
3. **Beautiful UI:** Make semantic web feel magical, not academic
4. **Developer Friendly:** Git-based workflow, APIs, extensibility
5. **Privacy Options:** Public, private, or federated hosting choices
6. **Open Standards:** RDF, SPARQL, standard ontologies
7. **Progressive Enhancement:** Start simple, add features incrementally

## Open Questions for v0.0.1

1. **Ontology Selection:** Which standard ontologies to map to?
2. **GLiNER Models:** Which pretrained models work best for general text?
3. **HTML Templates:** Custom or use existing framework?
4. **Local vs Cloud:** Start with local-first or cloud-first?
5. **Authentication:** GitHub only or support other providers?

## Related Projects & Context

- **CodeDoc:** Rob's existing RDF/ontology work for code analysis
- **MagicScroll:** SQLite/Oxigraph message storage system
- **Pixeltable:** Rob's current employer, potential backend
- **ASI-ARCH:** Research paper processing and evolution system

## Notes from Recent Frustrations

Google's LangExtract release (Oct 2025) performs comprehensive linguistic feature extraction - similar territory to what we're building. This reinforces the need to focus on what makes slop.at unique:
- Social/publishing layer (not just extraction)
- Beautiful UI and discovery (not just data)
- Git-based ownership and versioning
- Real-time collaborative evolution of ideas

---

**Next Steps:**
1. Set up basic project structure
2. Implement markdown → HTML pipeline
3. Integrate GLiNER for concept extraction
4. Test with sample documents
5. Iterate on HTML styling and UX
