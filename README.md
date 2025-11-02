# slop.at - Semantic Document Analysis

Transform text into beautiful, semantically-linked web pages with automatic concept extraction and graph-based discovery.

## ✨ What is slop.at?

slop.at is a **semantic web meets gist** experience that:

1. **Analyzes** text documents to detect type (conversation, markdown, etc.)
2. **Extracts** concepts using GLiNER across multiple ontologies (CS, Math, Philosophy, etc.)  
3. **Highlights** concepts with beautiful color-coded links in generated HTML
4. **Stores** semantic relationships in a graph database (Oxigraph)
5. **Enables** discovery of related content by clicking concept links

Think of it as turning any text into an interactive semantic map where concepts become clickable portals to related content.

## 🏗️ Architecture

```
Text Input → GLiNER Concept Extraction → Ontology Mapping → RDF Storage → Beautiful HTML
     ↓              ↓                      ↓                   ↓             ↓
Document      CS/Math/Philosophy      Standard Ontologies   Oxigraph    Color-coded
Analysis      Concept Detection       (FOAF, Dublin Core)   Database    Highlighting
```

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd slopat

# Install dependencies with uv (much faster!)
uv sync

# Test the pipeline
uv run python test_pipeline.py
```

## 🚀 Quick Start

### Process a single file:
```python
from slopat import process_file_simple
from pathlib import Path

result = process_file_simple(Path("my_document.txt"))
print(f"Generated: {result.saved_path}")
```

### Process text directly:
```python
from slopat import process_text_simple

text = """
Alice: I've been studying distributed consensus algorithms.
Bob: Raft is fascinating! Have you looked at the CAP theorem?
"""

result = process_text_simple(text)
print(f"Extracted {len(result.extraction_result.concepts)} concepts")
```

### Full pipeline with graph storage:
```python
from slopat import SlopProcessor
from pathlib import Path

processor = SlopProcessor(output_dir=Path("./output"))
result = processor.process_file(Path("conversation.txt"))

# Find related content
related = processor.find_related_slops("consensus algorithms")
print(f"Found {len(related)} related documents")
```

## 📄 Document Types Supported

- **Conversations**: Speaker-based dialogues (Alice:, Bob:)
- **Markdown**: Structured documents with headers
- **Plain Text**: General text documents
- **Structured**: Documents with clear formatting

## 🧠 Concept Ontologies

The system extracts concepts across multiple domains:

- **Computer Science**: Algorithms, data structures, systems
- **Mathematics**: Theorems, proofs, statistical methods  
- **Social Science**: Research methods, psychology, economics
- **Philosophy**: Concepts, ethics, logic
- **People & Organizations**: Named entities
- **Tools & Frameworks**: Software, methodologies

## 🎨 Color Coding

Each domain gets a distinct color in the generated HTML:
- 🔵 **Computer Science** → Blue
- 🟣 **Mathematics** → Purple  
- 🟢 **Social Science** → Green
- 🟡 **Philosophy** → Amber
- 🔴 **People** → Red
- 🔘 **Organizations** → Gray

## 📊 Graph Database

All semantic relationships are stored in Oxigraph using standard RDF ontologies:

```sparql
# Find documents discussing specific concepts
SELECT ?doc ?title WHERE {
  ?concept rdfs:label "consensus algorithms" .
  ?doc slop:discusses ?concept .
  OPTIONAL { ?doc dct:title ?title }
}

# Find co-occurring concepts  
SELECT ?related WHERE {
  ?concept1 rdfs:label "Raft" .
  ?concept1 slop:coOccursWith ?concept2 .
  ?concept2 rdfs:label ?related .
}
```

## 🌐 Generated HTML

Each processed document becomes a beautiful web page with:

- **Three-column layout**: Related content | Main content | Concept sidebar
- **Interactive highlighting**: Click concepts to discover related slops
- **Responsive design**: Works on desktop and mobile
- **Clean typography**: Optimized for reading

## 🛠️ Command Line Usage

```bash
# Process a single file
uv run slopat process document.txt

# Batch process a directory  
uv run slopat process data/

# Show statistics
uv run slopat stats

# Find related documents
uv run slopat related "consensus algorithms"

# Custom output directory
uv run slopat process document.txt --output ./my_output/
```

## 🔧 Configuration

The system uses sensible defaults but can be configured:

```python
from slopat import SlopProcessor
from slopat.graph import SlopStore

# Custom GLiNER model
processor = SlopProcessor(gliner_model="urchade/gliner_large")

# Custom graph store location
store = SlopStore(data_dir=Path("./my_graph_data"))
processor = SlopProcessor(store=store)

# Custom HTML styling
from slopat.web import HTMLGenerator

generator = HTMLGenerator(base_url="https://my-slop-site.com")
```

## 🧪 Example Output

Input text:
```
Alice: I've been exploring Raft consensus lately.
Bob: Have you looked at the CAP theorem implications?
```

Generated concepts:
- `Alice` (person_mention) 
- `Raft` (algorithm)
- `consensus` (computer_science_concept)
- `CAP theorem` (mathematics_concept)

HTML output: Beautiful page with blue highlighting for "Raft", purple for "CAP theorem", red for "Alice", etc.

## 🤝 Integration

slop.at is designed to integrate with:

- **Academic workflows**: Export RDF for research tools
- **Note-taking systems**: Process markdown/text notes
- **Documentation sites**: Add semantic navigation
- **Learning platforms**: Highlight key concepts

## 🎯 Roadmap

- [ ] **Vector embeddings** for semantic similarity
- [ ] **Web interface** for upload and browse
- [ ] **API endpoints** for integration
- [ ] **Custom ontologies** for domain-specific extraction
- [ ] **Cross-document linking** based on concept overlap
- [ ] **Export formats** (PDF, EPUB with semantic annotations)

## 📈 Performance

- **GLiNER inference**: ~100ms per document  
- **Graph storage**: Sub-second for typical documents
- **HTML generation**: Near-instant
- **Memory usage**: <500MB for typical workloads

## 🔍 Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from slopat import SlopProcessor
processor = SlopProcessor()
```

Check component status:
```python
stats = processor.get_statistics()
print(stats["components_loaded"])
```

## 📚 Academic Background

slop.at builds on established semantic web technologies:

- **GLiNER**: Generalist Named Entity Recognition
- **RDF/OWL**: Web Ontology Language for knowledge representation  
- **SPARQL**: Query language for semantic graphs
- **Standard Ontologies**: FOAF, Dublin Core, Computer Science Ontology

## 🏷️ License

[Your chosen license]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Submit a pull request

---

**Made with ❤️ for the semantic web**
