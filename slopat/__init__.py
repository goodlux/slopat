"""slop.at - Semantic document analysis and beautiful HTML generation"""

__version__ = "0.1.0"

from .main import SlopProcessor, process_file_simple, process_text_simple
from .parsers.text_parser import TextParser, DocumentType
from .parsers.gliner_extractor import ConceptExtractor, ExtractedConcept
from .parsers.ontology_mapper import OntologyMapper, SemanticMapping
from .graph.store import SlopStore
from .web.html_generator import HTMLGenerator, SlopPage

__all__ = [
    "SlopProcessor",
    "process_file_simple", 
    "process_text_simple",
    "TextParser",
    "DocumentType",
    "ConceptExtractor",
    "ExtractedConcept", 
    "OntologyMapper",
    "SemanticMapping",
    "SlopStore",
    "HTMLGenerator",
    "SlopPage"
]
