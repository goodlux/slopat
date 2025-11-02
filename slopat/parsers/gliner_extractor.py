"""GLiNER-based concept extraction for slop.at"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

try:
    from gliner import GLiNER
except ImportError:
    print("GLiNER not installed. Install with: pip install gliner")
    GLiNER = None

@dataclass
class ExtractedConcept:
    """Represents a concept extracted by GLiNER"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    context: str  # Surrounding text for disambiguation

@dataclass
class ConceptExtractionResult:
    """Results of concept extraction from a document"""
    concepts: List[ExtractedConcept]
    domain_distribution: Dict[str, int]
    concept_density: float
    processing_metadata: Dict[str, any]

class ConceptExtractor:
    """
    Extract concepts from text using GLiNER.
    Inspired by CodeDoc's AST extraction patterns.
    """
    
    def __init__(self, model_name: str = "urchade/gliner_base"):
        """Initialize GLiNER model with standard ontology labels"""
        if GLiNER is None:
            raise ImportError("GLiNER is required for concept extraction")
            
        self.model = GLiNER.from_pretrained(model_name)
        
        # Standard ontology labels for slop.at
        # These map to our domain ontologies
        self.ontology_labels = [
            # Computer Science
            "computer_science_concept",
            "algorithm", 
            "data_structure",
            "programming_language",
            "software_system",
            "distributed_system",
            "machine_learning_concept",
            
            # Mathematics  
            "mathematics_concept",
            "mathematical_theorem",
            "statistical_method",
            "mathematical_proof",
            "equation",
            
            # Social Sciences
            "social_science_concept",
            "research_method",
            "psychological_concept",
            "economic_concept",
            "organizational_behavior",
            
            # Philosophy
            "philosophical_concept",
            "ethical_principle",
            "logical_argument",
            "epistemological_concept",
            
            # General
            "person_mention",
            "organization",
            "academic_paper",
            "research_finding",
            "methodology",
            "tool",
            "framework",
        ]
        
        # Domain mappings for concept organization
        self.domain_mapping = {
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
    
    def extract_concepts(self, content: str, context_window: int = 50) -> ConceptExtractionResult:
        """
        Extract concepts from text content.
        Similar to CodeDoc's function extraction but for natural language.
        """
        # Clean and prepare text
        cleaned_content = self._preprocess_text(content)
        
        # Extract entities using GLiNER
        entities = self.model.predict_entities(
            cleaned_content, 
            self.ontology_labels,
            threshold=0.3  # Adjust based on precision/recall needs
        )
        
        # Convert to our concept format with context
        concepts = []
        for entity in entities:
            context = self._extract_context(
                cleaned_content, 
                entity['start'], 
                entity['end'], 
                context_window
            )
            
            concept = ExtractedConcept(
                text=entity['text'],
                label=entity['label'],
                start=entity['start'],
                end=entity['end'],
                confidence=entity.get('score', 0.0),
                context=context
            )
            concepts.append(concept)
        
        # Remove duplicates and overlaps
        concepts = self._deduplicate_concepts(concepts)
        
        # Calculate metadata
        domain_distribution = self._calculate_domain_distribution(concepts)
        concept_density = len(concepts) / len(cleaned_content.split()) if cleaned_content else 0
        
        processing_metadata = {
            'total_concepts': len(concepts),
            'unique_labels': len(set(c.label for c in concepts)),
            'avg_confidence': sum(c.confidence for c in concepts) / len(concepts) if concepts else 0,
            'content_length': len(cleaned_content),
        }
        
        return ConceptExtractionResult(
            concepts=concepts,
            domain_distribution=domain_distribution,
            concept_density=concept_density,
            processing_metadata=processing_metadata
        )
    
    def _preprocess_text(self, content: str) -> str:
        """Clean and prepare text for concept extraction"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove markdown formatting that might confuse GLiNER
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic
        content = re.sub(r'`(.*?)`', r'\1', content)        # Inline code
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)  # Code blocks
        
        return content.strip()
    
    def _extract_context(self, content: str, start: int, end: int, window: int) -> str:
        """Extract surrounding context for a concept"""
        context_start = max(0, start - window)
        context_end = min(len(content), end + window)
        return content[context_start:context_end].strip()
    
    def _deduplicate_concepts(self, concepts: List[ExtractedConcept]) -> List[ExtractedConcept]:
        """Remove duplicate and overlapping concepts"""
        # Sort by start position
        concepts.sort(key=lambda x: x.start)
        
        deduplicated = []
        for concept in concepts:
            # Check for overlap with existing concepts
            overlap = False
            for existing in deduplicated:
                if self._concepts_overlap(concept, existing):
                    # Keep the one with higher confidence
                    if concept.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(concept)
                    overlap = True
                    break
            
            if not overlap:
                deduplicated.append(concept)
        
        return deduplicated
    
    def _concepts_overlap(self, c1: ExtractedConcept, c2: ExtractedConcept) -> bool:
        """Check if two concepts overlap in text position"""
        return not (c1.end <= c2.start or c2.end <= c1.start)
    
    def _calculate_domain_distribution(self, concepts: List[ExtractedConcept]) -> Dict[str, int]:
        """Calculate distribution of concepts across domains"""
        distribution = {}
        for concept in concepts:
            domain = self.domain_mapping.get(concept.label, "other")
            distribution[domain] = distribution.get(domain, 0) + 1
        return distribution

def extract_concepts_from_file(file_path: Path) -> ConceptExtractionResult:
    """
    Extract concepts from a text file.
    Main entry point similar to CodeDoc's parse patterns.
    """
    extractor = ConceptExtractor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return extractor.extract_concepts(content)

if __name__ == "__main__":
    # Test concept extraction
    sample_text = """
    Alice: I've been exploring distributed consensus algorithms lately, particularly Raft and PBFT.
    
    Bob: That's fascinating! Raft is elegant because of its leader-election mechanism. Have you 
    looked into the CAP theorem implications?
    
    Alice: Yes, the trade-offs between consistency and availability are crucial. I'm also 
    interested in how game theory applies to Byzantine fault tolerance.
    
    Bob: Game theory is definitely relevant. Nash equilibria help analyze the strategic behavior 
    of malicious nodes in distributed systems.
    """
    
    try:
        extractor = ConceptExtractor()
        result = extractor.extract_concepts(sample_text)
        
        print(f"Extracted {len(result.concepts)} concepts:")
        for concept in result.concepts[:5]:  # Show first 5
            print(f"  {concept.text} ({concept.label}) - confidence: {concept.confidence:.2f}")
        
        print(f"\nDomain distribution: {result.domain_distribution}")
        print(f"Concept density: {result.concept_density:.3f}")
        
    except ImportError:
        print("GLiNER not available for testing")
