"""Beautiful HTML generation for slop.at with concept highlighting"""

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
class HighlightedSpan:
    """Represents a highlighted span in the text"""
    start: int
    end: int
    concept: ExtractedConcept
    css_class: str
    link_id: str

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
    Generate beautiful HTML pages with concept highlighting.
    Inspired by CodeDoc's HTML generation patterns.
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
        """
        Generate a complete slop.at page with concept highlighting.
        Main entry point for HTML generation.
        """
        # Generate unique URL path
        url_path = self._generate_url_path(content, file_path)
        
        # Create highlighted HTML content
        highlighted_content = self._highlight_concepts(content, extraction_result.concepts)
        
        # Generate page title
        title = self._generate_title(doc_metadata, file_path)
        
        # Create sidebar data
        sidebar_data = self._generate_sidebar_data(extraction_result, semantic_mapping)
        
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
            # Use file name for reproducible URLs
            base_name = file_path.stem
            clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '-', base_name)
            return f"/{clean_name}"
        else:
            # Use content hash for uploaded content
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            return f"/slop-{content_hash}"
    
    def _highlight_concepts(self, content: str, concepts: List[ExtractedConcept]) -> str:
        """Apply concept highlighting to text content"""
        # Sort concepts by start position (reverse order for replacement)
        sorted_concepts = sorted(concepts, key=lambda x: x.start, reverse=True)
        
        # Apply highlighting from end to beginning to preserve positions
        highlighted_content = content
        
        for concept in sorted_concepts:
            # Determine domain and CSS class
            domain = self._get_concept_domain(concept)
            css_class = self.concept_classes.get(domain, "concept-other")
            
            # Generate link ID for concept
            link_id = self._generate_concept_link_id(concept)
            
            # Extract the concept text
            concept_text = content[concept.start:concept.end]
            
            # Create highlighted span
            highlighted_span = f'''<span class="{css_class}" data-concept="{html.escape(concept.text)}" data-domain="{domain}" data-confidence="{concept.confidence:.2f}" data-link-id="{link_id}" onclick="selectConcept('{link_id}', '{html.escape(concept.text)}', '{domain}')">{html.escape(concept_text)}</span>'''
            
            # Replace in content
            highlighted_content = (
                highlighted_content[:concept.start] +
                highlighted_span +
                highlighted_content[concept.end:]
            )
        
        return highlighted_content
    
    def _get_concept_domain(self, concept: ExtractedConcept) -> str:
        """Map concept label to domain"""
        domain_mapping = {
            "computer_science_concept": "cs",
            "algorithm": "cs", 
            "data_structure": "cs",
            "programming_language": "cs",
            "software_system": "cs",
            "distributed_system": "cs",
            "machine_learning_concept": "cs",
            
            "mathematics_concept": "math",
            "mathematical_theorem": "math",
            "statistical_method": "math", 
            "mathematical_proof": "math",
            "equation": "math",
            
            "social_science_concept": "social",
            "research_method": "social",
            "psychological_concept": "social",
            "economic_concept": "social",
            "organizational_behavior": "social",
            
            "philosophical_concept": "philosophy",
            "ethical_principle": "philosophy",
            "logical_argument": "philosophy", 
            "epistemological_concept": "philosophy",
            
            "person_mention": "people",
            "organization": "entities",
            "academic_paper": "references",
            "research_finding": "findings",
            "methodology": "methods",
            "tool": "tools",
            "framework": "tools",
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
    
    def _generate_sidebar_data(
        self, 
        extraction_result: ConceptExtractionResult,
        semantic_mapping: SemanticMapping
    ) -> Dict:
        """Generate data for the sidebar"""
        # Group concepts by domain
        concepts_by_domain = {}
        for concept in extraction_result.concepts:
            domain = self._get_concept_domain(concept)
            if domain not in concepts_by_domain:
                concepts_by_domain[domain] = []
            concepts_by_domain[domain].append(concept)
        
        # Sort domains by concept count
        sorted_domains = sorted(
            concepts_by_domain.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        return {
            "concepts_by_domain": sorted_domains,
            "domain_distribution": extraction_result.domain_distribution,
            "concept_density": extraction_result.concept_density,
            "total_concepts": len(extraction_result.concepts),
            "processing_metadata": extraction_result.processing_metadata
        }
    
    def _generate_complete_html(
        self,
        highlighted_content: str,
        title: str,
        sidebar_data: Dict,
        doc_metadata: DocumentMetadata,
        url_path: str,
        outline: List[Dict]
    ) -> str:
        """Generate the complete HTML page"""
        
        # Generate CSS for concept highlighting
        concept_css = self._generate_concept_css()
        
        # Generate sidebar HTML
        concepts_sidebar_html = self._generate_concepts_sidebar_html(sidebar_data)
        
        # Generate outline HTML  
        outline_html = self._generate_outline_html(outline)
        
        # Process content based on document type
        processed_content, outline = self._process_content_by_type(highlighted_content, doc_metadata.doc_type)
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)} - slop.at</title>
    <meta name="description" content="Semantic document analysis by slop.at">
    
    <!-- Core Styles -->
    <style>
        {concept_css}
        
        /* Layout */
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.6;
        }}
        
        .container {{
            display: grid;
            grid-template-columns: 1fr 3fr 1fr;
            gap: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
        }}
        
        /* Header */
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
        
        /* Main Content */
        .main-content {{
            background: white;
            padding: 3rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            font-size: 1.1rem;
            line-height: 1.8;
        }}
        
        /* Sidebar */
        .sidebar {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            height: fit-content;
            position: sticky;
            top: 2rem;
        }}
        
        .sidebar h3 {{
            margin-top: 0;
            color: #374151;
            font-size: 1.1rem;
            border-bottom: 2px solid #f3f4f6;
            padding-bottom: 0.5rem;
        }}
        
        /* Related Content (Left Sidebar) */
        .related-content {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            height: fit-content;
            position: sticky;
            top: 2rem;
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
            font-size: 0.9rem;
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
            font-size: 0.85rem;
            transition: background-color 0.2s;
        }}
        
        .concept-item:hover {{
            background-color: #f9fafb;
        }}
        
        /* Stats */
        .stats {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #e5e7eb;
            font-size: 0.8rem;
            color: #6b7280;
        }}
        
        /* Responsive */
        @media (max-width: 1024px) {{
            .container {{
                grid-template-columns: 1fr;
                gap: 1rem;
            }}
            
            .sidebar, .related-content {{
                position: static;
            }}
        }}
        
        /* Conversation-specific styles */
        .conversation-line {{
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
            background: #f8fafc;
        }}
        
        .speaker {{
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 0.25rem;
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
        
        <aside class="related-content">
            <h3>🔗 Related Slops</h3>
            <div id="related-content">
                <p style="color: #6b7280; font-style: italic;">
                    Click a concept to discover related content
                </p>
            </div>
        </aside>
        
        <main class="main-content">
            {processed_content}
        </main>
        
        <aside class="sidebar">
            {sidebar_html}
        </aside>
    </div>
    
    <script>
        // Concept interaction handling
        function selectConcept(linkId, conceptText, domain) {{
            // Highlight selected concept
            document.querySelectorAll('.concept-selected').forEach(el => {{
                el.classList.remove('concept-selected');
            }});
            
            const element = document.querySelector(`[data-link-id="${{linkId}}"]`);
            if (element) {{
                element.classList.add('concept-selected');
            }}
            
            // Update related content (would connect to backend in real implementation)
            updateRelatedContent(conceptText, domain);
        }}
        
        function updateRelatedContent(conceptText, domain) {{
            const relatedDiv = document.getElementById('related-content');
            relatedDiv.innerHTML = `
                <div style="margin-bottom: 1rem;">
                    <strong>${{conceptText}}</strong> <span style="color: #6b7280;">(${{domain}})</span>
                </div>
                <div style="color: #6b7280; font-style: italic;">
                    Loading related slops...
                </div>
            `;
            
            // Here you would make an API call to find related documents
            // For now, just show a placeholder
            setTimeout(() => {{
                relatedDiv.innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <strong>${{conceptText}}</strong> <span style="color: #6b7280;">(${{domain}})</span>
                    </div>
                    <div style="color: #6b7280; font-style: italic;">
                        Related slops would appear here
                    </div>
                `;
            }}, 1000);
        }}
        
        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                document.querySelectorAll('.concept-selected').forEach(el => {{
                    el.classList.remove('concept-selected');
                }});
                document.getElementById('related-content').innerHTML = `
                    <p style="color: #6b7280; font-style: italic;">
                        Click a concept to discover related content
                    </p>
                `;
            }}
        }});
    </script>
</body>
</html>"""
        
        return html_template
    
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
            position: relative;
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
    
    def _generate_sidebar_html(self, sidebar_data: Dict) -> str:
        """Generate the concepts sidebar HTML"""
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
            
            # Sort concepts by confidence
            sorted_concepts = sorted(concepts, key=lambda x: x.confidence, reverse=True)
            
            for concept in sorted_concepts[:10]:  # Show top 10 per domain
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
            <h3>📊 Statistics</h3>
            <div>Concept Density: {sidebar_data['concept_density']:.3f}</div>
            <div>Total Concepts: {sidebar_data['total_concepts']}</div>
            <div>Domains: {len(sidebar_data['concepts_by_domain'])}</div>
        </div>""")
        
        return "\n".join(html_parts)
    
    def _process_content_by_type(self, content: str, doc_type: DocumentType) -> str:
        """Process content based on document type"""
        if doc_type == DocumentType.CONVERSATION:
            return self._format_conversation_content(content)
        elif doc_type == DocumentType.MARKDOWN:
            return self._format_markdown_content(content)
        else:
            # Plain text or structured - just wrap in paragraphs
            paragraphs = content.split('\n\n')
            return '\n'.join(f'<p>{paragraph.replace(chr(10), "<br>")}</p>' 
                           for paragraph in paragraphs if paragraph.strip())
    
    def _format_conversation_content(self, content: str) -> str:
        """Format conversation content with speaker identification"""
        lines = content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Check if line starts with a speaker pattern (Name:)
            speaker_match = re.match(r'^([A-Za-z][A-Za-z0-9_\s]*?):\s*(.*)', line)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2)
                formatted_lines.append(f"""
                <div class="conversation-line">
                    <div class="speaker">{html.escape(speaker)}:</div>
                    <div>{text}</div>
                </div>""")
            else:
                # Continuation of previous speaker or standalone text
                formatted_lines.append(f'<p>{line}</p>')
        
        return '\n'.join(formatted_lines)
    
    def _format_markdown_content(self, content: str) -> str:
        """Basic markdown formatting (subset)"""
        # This is a simplified markdown processor
        # For production, you'd want to use a proper markdown library
        
        # Headers
        content = re.sub(r'^### (.*$)', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*$)', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*$)', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        
        # Bold and italic
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        
        # Code blocks (basic)
        content = re.sub(r'`([^`]+)`', r'<code>\1</code>', content)
        
        # Paragraphs
        paragraphs = content.split('\n\n')
        return '\n'.join(f'<p>{paragraph.replace(chr(10), "<br>")}</p>' 
                       for paragraph in paragraphs if paragraph.strip())

def save_slop_page(slop_page: SlopPage, output_dir: Path) -> Path:
    """Save a slop page to disk"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create filename from URL path
    filename = slop_page.url_path.lstrip('/') + '.html'
    if not filename or filename == '.html':
        filename = 'index.html'
    
    file_path = output_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(slop_page.html_content)
    
    return file_path

if __name__ == "__main__":
    # Test HTML generation
    from ..parsers.gliner_extractor import ExtractedConcept, ConceptExtractionResult
    from ..parsers.text_parser import DocumentMetadata, DocumentType
    from ..parsers.ontology_mapper import SemanticMapping
    
    # Sample data
    sample_content = """Alice: I've been exploring distributed consensus algorithms lately, particularly Raft and PBFT.

Bob: That's fascinating! Raft is elegant because of its leader-election mechanism. Have you looked into the CAP theorem implications?

Alice: Yes, the trade-offs between consistency and availability are crucial. I'm also interested in how game theory applies to Byzantine fault tolerance.

Bob: Game theory is definitely relevant. Nash equilibria help analyze the strategic behavior of malicious nodes in distributed systems."""
    
    concepts = [
        ExtractedConcept("Alice", "person_mention", 0, 5, 0.9, "Alice: I've been exploring"),
        ExtractedConcept("Raft", "algorithm", 65, 69, 0.9, "particularly Raft and PBFT"),
        ExtractedConcept("PBFT", "algorithm", 74, 78, 0.8, "particularly Raft and PBFT"),
        ExtractedConcept("Bob", "person_mention", 81, 84, 0.9, "Bob: That's fascinating"),
        ExtractedConcept("CAP theorem", "mathematics_concept", 200, 211, 0.8, "looked into the CAP theorem"),
        ExtractedConcept("game theory", "mathematics_concept", 350, 361, 0.9, "how game theory applies"),
    ]
    
    extraction_result = ConceptExtractionResult(
        concepts=concepts,
        domain_distribution={"cs": 3, "math": 2, "people": 2},
        concept_density=0.05,
        processing_metadata={"total_concepts": 6}
    )
    
    doc_metadata = DocumentMetadata(
        DocumentType.CONVERSATION,
        0.9,
        {"has_speakers": True, "line_count": 4},
        "Distributed Consensus Discussion"
    )
    
    # Generate HTML
    generator = HTMLGenerator()
    slop_page = generator.generate_slop_page(
        sample_content,
        extraction_result,
        doc_metadata,
        SemanticMapping([], {}, 0, 0)  # Empty semantic mapping for test
    )
    
    print(f"Generated page: {slop_page.title}")
    print(f"URL path: {slop_page.url_path}")
    print(f"Concepts: {len(slop_page.concepts)}")
    
    # Save to output directory
    output_dir = Path("../../output")
    saved_path = save_slop_page(slop_page, output_dir)
    print(f"Saved to: {saved_path}")
