"""Simplified HTML generation for markdown-focused slop.at"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import html
import re
from urllib.parse import quote

from ..parsers.gliner_extractor import ExtractedConcept, ConceptExtractionResult
from ..parsers.text_parser import DocumentMetadata, DocumentType
from ..parsers.ontology_mapper import SemanticMapping

@dataclass
class DocumentOutline:
    """Document outline item"""
    level: int
    text: str
    id: str
    line_number: int

@dataclass
class SlopPage:
    """A generated slop.at page"""
    html_content: str
    url_path: str
    title: str
    concepts: List[ExtractedConcept]
    metadata: DocumentMetadata

class HTMLGenerator:
    """
    Generate beautiful HTML pages with 3-column layout:
    stacked left sidebars | content | outline
    """
    
    def __init__(self, base_url: str = "https://slop.at"):
        self.base_url = base_url
        
        # Domain color mappings for concept highlighting
        self.domain_colors = {
            "cs": "#3B82F6",           # Blue for Computer Science
            "math": "#8B5CF6",         # Purple for Mathematics  
            "social": "#10B981",       # Green for Social Science
            "philosophy": "#F59E0B",   # Amber for Philosophy
            "people": "#EF4444",       # Red for People
            "entities": "#6B7280",     # Gray for Organizations
            "references": "#EC4899",   # Pink for Papers/References
            "findings": "#84CC16",     # Lime for Research Findings
            "methods": "#06B6D4",      # Cyan for Methodologies
            "tools": "#8B5A2B",       # Brown for Tools/Frameworks
            "other": "#6B7280"         # Gray for Other
        }
        
        # CSS classes for concept types
        self.concept_classes = {
            "cs": "concept-cs",
            "math": "concept-math", 
            "social": "concept-social",
            "philosophy": "concept-philosophy",
            "people": "concept-people",
            "entities": "concept-entities",
            "references": "concept-references",
            "findings": "concept-findings",
            "methods": "concept-methods",
            "tools": "concept-tools",
            "other": "concept-other"
        }
    
    def generate_slop_page(
        self,
        content: str,
        extraction_result: ConceptExtractionResult,
        doc_metadata: DocumentMetadata,
        semantic_mapping: SemanticMapping,
        file_path: Optional[Path] = None
    ) -> SlopPage:
        """Generate a complete slop.at page with optimized 3-column layout"""

        # Generate unique URL path
        url_path = self._generate_url_path(content, file_path)

        # Generate page title
        title = self._generate_title(doc_metadata, file_path)

        # Create sidebar data
        sidebar_data = self._generate_sidebar_data(extraction_result, semantic_mapping)

        # SIMPLIFIED FLOW:
        # 1. Convert markdown to HTML first
        processed_content, outline = self._process_content_by_type(content, doc_metadata.doc_type)

        # 2. Highlight concepts in the HTML (text-based search, not positions)
        highlighted_content = self._highlight_concepts_in_html(processed_content, extraction_result.concepts)

        # Generate complete HTML page
        html_content = self._generate_complete_html(
            highlighted_content,
            title,
            sidebar_data,
            doc_metadata,
            url_path,
            outline
        )

        return SlopPage(
            html_content=html_content,
            url_path=url_path,
            title=title,
            concepts=extraction_result.concepts,
            metadata=doc_metadata
        )
    
    def _generate_url_path(self, content: str, file_path: Optional[Path] = None) -> str:
        """Generate a unique URL path for the slop"""
        if file_path:
            base_name = file_path.stem
            clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', base_name)
            return f"/{clean_name}"
        else:
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            return f"/slop-{content_hash}"
    
    def _expand_to_word_boundaries(self, content: str, start: int, end: int) -> Tuple[int, int]:
        """Expand concept boundaries to include full words

        GLiNER often detects partial words, so we expand the span to word boundaries.
        Avoids expanding into markdown syntax characters.
        """
        # Characters that should stop word boundary expansion (markdown syntax)
        stop_chars = {'#', '*', '_', '`', '[', ']', '(', ')', '\n', '\r'}

        # Expand left to word boundary (but not past markdown syntax or newlines)
        while start > 0:
            prev_char = content[start - 1]
            if prev_char in stop_chars or not (prev_char.isalnum() or prev_char in {' ', '-'}):
                break
            if prev_char == ' ':
                # Don't include leading space
                break
            start -= 1

        # Expand right to word boundary (but not past markdown syntax or newlines)
        while end < len(content):
            next_char = content[end]
            if next_char in stop_chars or not (next_char.isalnum() or next_char in {' ', '-'}):
                break
            if next_char == ' ':
                # Don't include trailing space
                break
            end += 1

        return start, end

    def _highlight_concepts(self, content: str, concepts: List[ExtractedConcept]) -> str:
        """Apply concept highlighting to text content

        Expands concept boundaries to word boundaries to avoid partial word highlighting.
        """
        sorted_concepts = sorted(concepts, key=lambda x: x.start, reverse=True)
        highlighted_content = content

        for concept in sorted_concepts:
            # Expand to word boundaries
            expanded_start, expanded_end = self._expand_to_word_boundaries(
                content, concept.start, concept.end
            )

            domain = self._get_concept_domain(concept)
            css_class = self.concept_classes.get(domain, "concept-other")
            link_id = self._generate_concept_link_id(concept)
            concept_text = content[expanded_start:expanded_end]

            highlighted_span = f'''<span class="{css_class}" data-concept="{html.escape(concept.text)}" data-domain="{domain}" data-confidence="{concept.confidence:.2f}" data-link-id="{link_id}" onclick="selectConcept('{link_id}', '{html.escape(concept.text)}', '{domain}')">{html.escape(concept_text)}</span>'''

            highlighted_content = (
                highlighted_content[:expanded_start] +
                highlighted_span +
                highlighted_content[expanded_end:]
            )

        return highlighted_content

    def _highlight_concepts_in_html(self, html_content: str, concepts: List[ExtractedConcept]) -> str:
        """Highlight concepts with simple regex replacement on HTML

        Dead simple: just find concept text and wrap it in a span.
        Sort by length to avoid partial matches.
        """
        # Sort by length (longest first) to avoid partial matches
        sorted_concepts = sorted(concepts, key=lambda x: len(x.text), reverse=True)

        highlighted_texts = set()
        result = html_content

        for concept in sorted_concepts:
            # Skip duplicates
            if concept.text.lower() in highlighted_texts:
                continue

            domain = self._get_concept_domain(concept)
            css_class = self.concept_classes.get(domain, "concept-other")
            link_id = self._generate_concept_link_id(concept)

            # Simple regex: find the concept text (case insensitive, whole word)
            # Use \b for word boundaries to avoid partial matches
            pattern = re.compile(r'\b(' + re.escape(concept.text) + r')\b', re.IGNORECASE)

            # Build the replacement span
            replacement = f'<span class="{css_class}" data-concept="{html.escape(concept.text)}" data-domain="{domain}" data-confidence="{concept.confidence:.2f}" data-link-id="{link_id}" onclick="selectConcept(\'{link_id}\', \'{html.escape(concept.text)}\', \'{domain}\')">' + r'\1' + '</span>'

            # Replace first occurrence only to avoid duplicates
            result = pattern.sub(replacement, result, count=1)
            highlighted_texts.add(concept.text.lower())

        return result

    def _get_concept_domain(self, concept: ExtractedConcept) -> str:
        """Map concept label to domain"""
        domain_mapping = {
            "computer_science_concept": "cs", "algorithm": "cs", "data_structure": "cs",
            "programming_language": "cs", "software_system": "cs", "distributed_system": "cs",
            "machine_learning_concept": "cs", "mathematics_concept": "math", "mathematical_theorem": "math",
            "statistical_method": "math", "mathematical_proof": "math", "equation": "math",
            "social_science_concept": "social", "research_method": "social", "psychological_concept": "social",
            "economic_concept": "social", "organizational_behavior": "social", "philosophical_concept": "philosophy",
            "ethical_principle": "philosophy", "logical_argument": "philosophy", "epistemological_concept": "philosophy",
            "person_mention": "people", "organization": "entities", "academic_paper": "references",
            "research_finding": "findings", "methodology": "methods", "tool": "tools", "framework": "tools",
        }
        return domain_mapping.get(concept.label, "other")
    
    def _generate_concept_link_id(self, concept: ExtractedConcept) -> str:
        """Generate unique link ID for concept"""
        concept_id = hashlib.sha256(f"{concept.text}_{concept.label}".encode()).hexdigest()[:8]
        return f"concept-{concept_id}"
    
    def _generate_title(self, doc_metadata: DocumentMetadata, file_path: Optional[Path] = None) -> str:
        """Generate page title"""
        if doc_metadata.suggested_title:
            return doc_metadata.suggested_title
        elif file_path:
            return file_path.stem.replace('-', ' ').replace('_', ' ').title()
        else:
            return f"{doc_metadata.doc_type.value.title()} Document"
    
    def _generate_sidebar_data(self, extraction_result: ConceptExtractionResult, semantic_mapping: SemanticMapping) -> Dict:
        """Generate data for the concepts sidebar"""
        concepts_by_domain = {}
        for concept in extraction_result.concepts:
            domain = self._get_concept_domain(concept)
            if domain not in concepts_by_domain:
                concepts_by_domain[domain] = []
            concepts_by_domain[domain].append(concept)
        
        sorted_domains = sorted(concepts_by_domain.items(), key=lambda x: len(x[1]), reverse=True)
        
        return {
            "concepts_by_domain": sorted_domains,
            "domain_distribution": extraction_result.domain_distribution,
            "concept_density": extraction_result.concept_density,
            "total_concepts": len(extraction_result.concepts),
            "processing_metadata": extraction_result.processing_metadata
        }
    
    def _process_content_by_type(self, content: str, doc_type: DocumentType) -> Tuple[str, List[DocumentOutline]]:
        """Process content based on document type and extract outline"""
        return self._format_markdown_content(content)
    
    def _format_markdown_content(self, content: str) -> Tuple[str, List[DocumentOutline]]:
        """Format markdown content using Python's markdown library"""
        import markdown
        from markdown.extensions import Extension
        from markdown.treeprocessors import Treeprocessor
        import xml.etree.ElementTree as etree

        outline = []

        # Custom extension to add IDs to headers and extract outline
        class OutlineExtractor(Treeprocessor):
            def run(self, root):
                for elem in root.iter():
                    if elem.tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        level = int(elem.tag[1])
                        text = ''.join(elem.itertext())
                        outline_id = f"heading-{len(outline)}"
                        elem.set('id', outline_id)
                        outline.append(DocumentOutline(level, text, outline_id, 0))
                return root

        class OutlineExtension(Extension):
            def extendMarkdown(self, md):
                md.treeprocessors.register(OutlineExtractor(md), 'outline', 15)

        # Use markdown library to convert
        md = markdown.Markdown(extensions=['extra', OutlineExtension()])
        html = md.convert(content)

        return html, outline
    
    def _generate_complete_html(
        self,
        processed_content: str,
        title: str,
        sidebar_data: Dict,
        doc_metadata: DocumentMetadata,
        url_path: str,
        outline: List[DocumentOutline]
    ) -> str:
        """Generate the complete HTML page with optimized 3-column layout"""
        
        # Generate component HTML
        concept_css = self._generate_concept_css()
        left_sidebar_html = self._generate_left_sidebar_html(sidebar_data)
        outline_html = self._generate_outline_html(outline)
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} - slop.at</title>
    <meta name="description" content="Semantic document analysis by slop.at">
    
    <style>
        {concept_css}
        
        /* Optimized 3-column layout */
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.6;
        }}
        
        .container {{
            display: grid;
            grid-template-columns: 300px 1fr 280px;
            gap: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem 1rem;
            min-height: 100vh;
        }}
        
        /* Header spans all columns */
        .header {{
            grid-column: 1 / -1;
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 600;
            color: #111827;
        }}
        
        .header .subtitle {{
            margin-top: 0.5rem;
            color: #6b7280;
            font-size: 0.9rem;
        }}
        
        /* Left Sidebar - Stacked */
        .left-sidebar {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            height: fit-content;
            position: sticky;
            top: 2rem;
        }}
        
        .sidebar-section {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            font-size: 0.85rem;
        }}
        
        /* Main Content */
        .main-content {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            font-size: 1.1rem;
            line-height: 1.8;
            overflow-x: auto;
        }}
        
        /* Right Sidebar - Outline */
        .right-sidebar {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            height: fit-content;
            position: sticky;
            top: 2rem;
            font-size: 0.85rem;
        }}
        
        /* Sidebar Headers */
        .sidebar h3 {{
            margin-top: 0;
            margin-bottom: 1rem;
            color: #374151;
            font-size: 1rem;
            border-bottom: 2px solid #f3f4f6;
            padding-bottom: 0.5rem;
        }}
        
        /* Domain Groups */
        .domain-group {{
            margin-bottom: 1.5rem;
        }}
        
        .domain-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        
        .concept-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .concept-item {{
            margin: 0.25rem 0;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: background-color 0.2s;
        }}
        
        .concept-item:hover {{
            background-color: #f9fafb;
        }}
        
        /* Outline Styles */
        .outline-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        
        .outline-item {{
            margin: 0.25rem 0;
            transition: all 0.2s;
        }}
        
        .outline-link {{
            display: block;
            padding: 0.25rem 0.5rem;
            color: #4b5563;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.8rem;
            line-height: 1.3;
        }}
        
        .outline-link:hover {{
            background-color: #f3f4f6;
            color: #1f2937;
        }}
        
        .outline-item.level-1 {{ margin-left: 0; font-weight: 600; }}
        .outline-item.level-2 {{ margin-left: 1rem; }}
        .outline-item.level-3 {{ margin-left: 2rem; }}
        .outline-item.level-4 {{ margin-left: 3rem; }}
        
        /* Stats */
        .stats {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e7eb;
            font-size: 0.75rem;
            color: #6b7280;
        }}
        
        /* Related Content */
        .related-content {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e7eb;
        }}
        
        /* Responsive */
        @media (max-width: 1200px) {{
            .container {{
                grid-template-columns: 280px 1fr 240px;
                gap: 1.5rem;
            }}
        }}
        
        @media (max-width: 1000px) {{
            .container {{
                grid-template-columns: 1fr;
                gap: 1rem;
                padding: 1rem 0.5rem;
            }}
            
            .left-sidebar,
            .right-sidebar {{
                position: static;
                order: 2;
            }}
            
            .main-content {{
                order: 1;
                padding: 2rem 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>{html.escape(title)}</h1>
            <div class="subtitle">
                {doc_metadata.doc_type.value.title()} · 
                {len(sidebar_data['concepts_by_domain'])} domains · 
                {sidebar_data['total_concepts']} concepts
            </div>
        </header>
        
        <aside class="left-sidebar">
            {left_sidebar_html}
        </aside>
        
        <main class="main-content">
            {processed_content}
        </main>
        
        <aside class="right-sidebar">
            {outline_html}
        </aside>
    </div>
    
    <script>
        function selectConcept(linkId, conceptText, domain) {{
            // Highlight selected concept
            document.querySelectorAll('.concept-selected').forEach(el => {{
                el.classList.remove('concept-selected');
            }});
            
            const element = document.querySelector(`[data-link-id="${{linkId}}"]`);
            if (element) {{
                element.classList.add('concept-selected');
            }}
            
            // Update related content
            updateRelatedContent(conceptText, domain);
        }}
        
        function updateRelatedContent(conceptText, domain) {{
            const relatedDiv = document.getElementById('related-content');
            if (relatedDiv) {{
                relatedDiv.innerHTML = `
                    <div style="margin-bottom: 0.5rem; font-weight: 600; font-size: 0.8rem;">
                        ${{conceptText}}
                    </div>
                    <div style="color: #6b7280; font-size: 0.75rem; margin-bottom: 0.5rem;">
                        ${{domain}} concept
                    </div>
                    <div style="color: #6b7280; font-style: italic; font-size: 0.7rem;">
                        Related content will appear here when cross-document linking is implemented
                    </div>
                `;
            }}
        }}
        
        // Smooth scrolling for outline links
        document.addEventListener('click', (e) => {{
            if (e.target.classList.contains('outline-link')) {{
                e.preventDefault();
                const targetId = e.target.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }}
        }});
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                document.querySelectorAll('.concept-selected').forEach(el => {{
                    el.classList.remove('concept-selected');
                }});
                const relatedDiv = document.getElementById('related-content');
                if (relatedDiv) {{
                    relatedDiv.innerHTML = `
                        <p style="color: #6b7280; font-style: italic; font-size: 0.7rem;">
                            Click a concept to discover related content
                        </p>
                    `;
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    def _generate_concept_css(self) -> str:
        """Generate CSS for concept highlighting"""
        css_rules = []
        for domain, color in self.domain_colors.items():
            css_class = self.concept_classes.get(domain, "concept-other")
            css_rules.append(f"""
        .{css_class} {{
            background-color: {color}20;
            border-bottom: 2px solid {color};
            padding: 0.1rem 0.2rem;
            border-radius: 3px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .{css_class}:hover {{
            background-color: {color}40;
            transform: translateY(-1px);
        }}
        
        .{css_class}.concept-selected {{
            background-color: {color}60;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .domain-title.{css_class} {{
            background-color: {color}30;
            color: {color};
            border-left: 3px solid {color};
        }}""")
        return "\n".join(css_rules)
    
    def _generate_left_sidebar_html(self, sidebar_data: Dict) -> str:
        """Generate the stacked left sidebar HTML"""
        concepts_html = self._generate_concepts_section_html(sidebar_data)
        return f"""
        <div class="sidebar-section">
            {concepts_html}
        </div>
        <div class="sidebar-section">
            <h3>🔗 Related Slops</h3>
            <div id="related-content">
                <p style="color: #6b7280; font-style: italic; font-size: 0.7rem;">
                    Click a concept to discover related content
                </p>
            </div>
        </div>
        """
    
    def _generate_concepts_section_html(self, sidebar_data: Dict) -> str:
        """Generate the concepts section HTML"""
        html_parts = ["<h3>📝 Concepts</h3>"]
        
        for domain, concepts in sidebar_data["concepts_by_domain"]:
            domain_title = domain.replace('_', ' ').title()
            css_class = self.concept_classes.get(domain, "concept-other")
            
            html_parts.append(f"""
            <div class="domain-group">
                <div class="domain-title {css_class}">
                    {domain_title} ({len(concepts)})
                </div>
                <ul class="concept-list">""")
            
            sorted_concepts = sorted(concepts, key=lambda x: x.confidence, reverse=True)
            
            for concept in sorted_concepts[:6]:  # Show top 6 per domain
                link_id = self._generate_concept_link_id(concept)
                html_parts.append(f"""
                    <li class="concept-item {css_class}" 
                        onclick="selectConcept('{link_id}', '{html.escape(concept.text)}', '{domain}')"
                        title="Confidence: {concept.confidence:.2f}">
                        {html.escape(concept.text)}
                    </li>""")
            
            html_parts.append("</ul></div>")
        
        # Add statistics
        html_parts.append(f"""
        <div class="stats">
            <div><strong>Stats</strong></div>
            <div>Concepts: {sidebar_data['total_concepts']}</div>
            <div>Domains: {len(sidebar_data['concepts_by_domain'])}</div>
            <div>Density: {sidebar_data['concept_density']:.3f}</div>
        </div>""")
        
        return "\n".join(html_parts)
    
    def _generate_outline_html(self, outline: List[DocumentOutline]) -> str:
        """Generate the document outline HTML"""
        if not outline:
            return """
            <h3>📋 Outline</h3>
            <p style="color: #6b7280; font-style: italic; font-size: 0.7rem;">
                No structure detected
            </p>
            """
        
        html_parts = ["<h3>📋 Outline</h3>", "<ul class=\"outline-list\">"]
        
        for item in outline:
            html_parts.append(f"""
                <li class="outline-item level-{item.level}">
                    <a href="#{item.id}" class="outline-link">
                        {html.escape(item.text)}
                    </a>
                </li>""")
        
        html_parts.append("</ul>")
        return "\n".join(html_parts)

def save_slop_page(slop_page: SlopPage, output_dir: Path) -> Path:
    """Save a slop page to disk"""
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = slop_page.url_path.lstrip('/') + '.html'
    if not filename or filename == '.html':
        filename = 'index.html'
    
    file_path = output_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(slop_page.html_content)
    
    return file_path
