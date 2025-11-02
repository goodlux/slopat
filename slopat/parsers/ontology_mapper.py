"""Map extracted concepts to standard ontologies and generate RDF"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import hashlib
import uuid
from urllib.parse import quote

from .gliner_extractor import ExtractedConcept, ConceptExtractionResult
from .text_parser import DocumentMetadata, DocumentType

@dataclass
class RDFTriple:
    """Represents an RDF triple"""
    subject: str
    predicate: str
    object: str
    object_type: str = "uri"  # "uri", "literal", "typed_literal"
    datatype: Optional[str] = None

@dataclass 
class SemanticMapping:
    """Results of mapping concepts to semantic ontologies"""
    triples: List[RDFTriple]
    namespaces: Dict[str, str]
    concepts_mapped: int
    relationships_created: int

class OntologyMapper:
    """
    Map GLiNER concepts to standard ontologies and generate RDF.
    Inspired by CodeDoc's ontology mapping patterns.
    """
    
    def __init__(self):
        # Standard namespace prefixes
        self.namespaces = {
            "slop": "http://slop.at/ontology#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "foaf": "http://xmlns.com/foaf/0.1/",
            "dct": "http://purl.org/dc/terms/",
            "cso": "http://cso.kmi.open.ac.uk/",  # Computer Science Ontology
            "msc": "http://msc2010.org/",        # Mathematics Subject Classification
            "schema": "http://schema.org/",
        }
        
        # Concept mappings to standard ontologies
        self.concept_mappings = {
            # Computer Science concepts
            "computer_science_concept": "cso:ComputerScience",
            "algorithm": "cso:Algorithm", 
            "data_structure": "cso:DataStructure",
            "programming_language": "cso:ProgrammingLanguage",
            "software_system": "cso:SoftwareSystem",
            "distributed_system": "cso:DistributedSystem",
            "machine_learning_concept": "cso:MachineLearning",
            
            # Mathematics concepts
            "mathematics_concept": "msc:Mathematics",
            "mathematical_theorem": "msc:Theorem",
            "statistical_method": "msc:Statistics",
            "mathematical_proof": "msc:Proof",
            "equation": "msc:Equation",
            
            # Social Science concepts  
            "social_science_concept": "schema:SocialScience",
            "research_method": "schema:ResearchMethod",
            "psychological_concept": "schema:Psychology",
            "economic_concept": "schema:Economics",
            "organizational_behavior": "schema:Organization",
            
            # Philosophy concepts
            "philosophical_concept": "schema:Philosophy",
            "ethical_principle": "schema:Ethics",
            "logical_argument": "schema:Logic",
            "epistemological_concept": "schema:Epistemology",
            
            # General concepts
            "person_mention": "foaf:Person",
            "organization": "foaf:Organization", 
            "academic_paper": "schema:ScholarlyArticle",
            "research_finding": "schema:ResearchFindings",
            "methodology": "schema:ResearchMethod",
            "tool": "schema:SoftwareApplication",
            "framework": "schema:SoftwareApplication",
        }
    
    def map_to_ontologies(
        self, 
        content: str,
        extraction_result: ConceptExtractionResult,
        doc_metadata: DocumentMetadata,
        file_path: Optional[Path] = None
    ) -> SemanticMapping:
        """
        Map extracted concepts to RDF triples.
        Main entry point similar to CodeDoc's ontology mapping.
        """
        triples = []
        
        # Generate unique URIs
        doc_uri = self._generate_document_uri(content, file_path)
        
        # Create document metadata triples
        doc_triples = self._create_document_triples(doc_uri, doc_metadata, file_path)
        triples.extend(doc_triples)
        
        # Create concept triples
        concept_triples, concept_uris = self._create_concept_triples(
            doc_uri, extraction_result.concepts
        )
        triples.extend(concept_triples)
        
        # Create relationship triples
        relationship_triples = self._create_relationship_triples(
            doc_uri, concept_uris, extraction_result.concepts
        )
        triples.extend(relationship_triples)
        
        # Create domain distribution triples
        domain_triples = self._create_domain_triples(
            doc_uri, extraction_result.domain_distribution
        )
        triples.extend(domain_triples)
        
        relationships_created = len(relationship_triples) + len(domain_triples)
        
        return SemanticMapping(
            triples=triples,
            namespaces=self.namespaces,
            concepts_mapped=len(extraction_result.concepts),
            relationships_created=relationships_created
        )
    
    def _generate_document_uri(self, content: str, file_path: Optional[Path] = None) -> str:
        """Generate a unique URI for the document"""
        if file_path:
            # Use file path for reproducible URIs
            identifier = str(file_path.stem)
        else:
            # Use content hash for uploaded content
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
            identifier = f"doc-{content_hash}"
        
        return f"{self.namespaces['slop']}document/{quote(identifier)}"
    
    def _create_document_triples(
        self, 
        doc_uri: str, 
        doc_metadata: DocumentMetadata,
        file_path: Optional[Path] = None
    ) -> List[RDFTriple]:
        """Create RDF triples for document metadata"""
        triples = []
        
        # Basic document type
        triples.append(RDFTriple(
            doc_uri, 
            "rdf:type", 
            "slop:Document"
        ))
        
        # Document type classification
        doc_type_uri = f"slop:{doc_metadata.doc_type.value.title()}Document"
        triples.append(RDFTriple(
            doc_uri,
            "rdf:type", 
            doc_type_uri
        ))
        
        # Confidence score
        triples.append(RDFTriple(
            doc_uri,
            "slop:typeConfidence",
            str(doc_metadata.confidence),
            object_type="typed_literal",
            datatype="http://www.w3.org/2001/XMLSchema#float"
        ))
        
        # Title if available
        if doc_metadata.suggested_title:
            triples.append(RDFTriple(
                doc_uri,
                "dct:title",
                doc_metadata.suggested_title,
                object_type="literal"
            ))
        
        # Features as data properties
        for key, value in doc_metadata.features.items():
            if isinstance(value, (int, float)):
                triples.append(RDFTriple(
                    doc_uri,
                    f"slop:{key}",
                    str(value),
                    object_type="typed_literal",
                    datatype="http://www.w3.org/2001/XMLSchema#float" if isinstance(value, float) else "http://www.w3.org/2001/XMLSchema#integer"
                ))
            elif isinstance(value, bool):
                triples.append(RDFTriple(
                    doc_uri,
                    f"slop:{key}",
                    str(value).lower(),
                    object_type="typed_literal", 
                    datatype="http://www.w3.org/2001/XMLSchema#boolean"
                ))
        
        # File path if available
        if file_path:
            triples.append(RDFTriple(
                doc_uri,
                "slop:filePath", 
                str(file_path),
                object_type="literal"
            ))
        
        return triples
    
    def _create_concept_triples(
        self, 
        doc_uri: str, 
        concepts: List[ExtractedConcept]
    ) -> Tuple[List[RDFTriple], List[str]]:
        """Create RDF triples for extracted concepts"""
        triples = []
        concept_uris = []
        
        for concept in concepts:
            # Generate concept URI
            concept_id = hashlib.sha256(f"{concept.text}_{concept.label}".encode()).hexdigest()[:8]
            concept_uri = f"{self.namespaces['slop']}concept/{concept_id}"
            concept_uris.append(concept_uri)
            
            # Basic concept type
            triples.append(RDFTriple(
                concept_uri,
                "rdf:type",
                "slop:Concept"
            ))
            
            # Map to standard ontology
            if concept.label in self.concept_mappings:
                ontology_type = self.concept_mappings[concept.label]
                triples.append(RDFTriple(
                    concept_uri,
                    "rdf:type",
                    ontology_type
                ))
            
            # Concept text
            triples.append(RDFTriple(
                concept_uri,
                "rdfs:label",
                concept.text,
                object_type="literal"
            ))
            
            # GLiNER label
            triples.append(RDFTriple(
                concept_uri,
                "slop:glinerLabel",
                concept.label,
                object_type="literal"
            ))
            
            # Confidence score
            triples.append(RDFTriple(
                concept_uri,
                "slop:confidence",
                str(concept.confidence),
                object_type="typed_literal",
                datatype="http://www.w3.org/2001/XMLSchema#float"
            ))
            
            # Position in text
            triples.append(RDFTriple(
                concept_uri,
                "slop:startPosition",
                str(concept.start),
                object_type="typed_literal",
                datatype="http://www.w3.org/2001/XMLSchema#integer"
            ))
            
            triples.append(RDFTriple(
                concept_uri,
                "slop:endPosition", 
                str(concept.end),
                object_type="typed_literal",
                datatype="http://www.w3.org/2001/XMLSchema#integer"
            ))
            
            # Context
            triples.append(RDFTriple(
                concept_uri,
                "slop:context",
                concept.context,
                object_type="literal"
            ))
            
            # Link concept to document
            triples.append(RDFTriple(
                doc_uri,
                "slop:discusses",
                concept_uri
            ))
        
        return triples, concept_uris
    
    def _create_relationship_triples(
        self,
        doc_uri: str,
        concept_uris: List[str], 
        concepts: List[ExtractedConcept]
    ) -> List[RDFTriple]:
        """Create relationship triples between concepts"""
        triples = []
        
        # Co-occurrence relationships
        for i, concept_a in enumerate(concepts):
            for j, concept_b in enumerate(concepts[i+1:], i+1):
                # Check if concepts are nearby (within 100 characters)
                distance = abs(concept_a.start - concept_b.start)
                if distance < 100:
                    triples.append(RDFTriple(
                        concept_uris[i],
                        "slop:coOccursWith",
                        concept_uris[j]
                    ))
        
        return triples
    
    def _create_domain_triples(
        self,
        doc_uri: str,
        domain_distribution: Dict[str, int]
    ) -> List[RDFTriple]:
        """Create triples for domain classification"""
        triples = []
        
        total_concepts = sum(domain_distribution.values())
        
        for domain, count in domain_distribution.items():
            if total_concepts > 0:
                percentage = count / total_concepts
                
                # Domain coverage
                triples.append(RDFTriple(
                    doc_uri,
                    f"slop:covers{domain.title()}",
                    str(percentage),
                    object_type="typed_literal",
                    datatype="http://www.w3.org/2001/XMLSchema#float"
                ))
                
                # Primary domain if > 50%
                if percentage > 0.5:
                    triples.append(RDFTriple(
                        doc_uri,
                        "slop:primaryDomain",
                        domain,
                        object_type="literal"
                    ))
        
        return triples

def serialize_triples_turtle(mapping: SemanticMapping) -> str:
    """Serialize RDF triples to Turtle format"""
    lines = []
    
    # Add namespace prefixes
    for prefix, uri in mapping.namespaces.items():
        lines.append(f"@prefix {prefix}: <{uri}> .")
    lines.append("")
    
    # Group triples by subject
    subjects = {}
    for triple in mapping.triples:
        if triple.subject not in subjects:
            subjects[triple.subject] = []
        subjects[triple.subject].append(triple)
    
    # Serialize each subject
    for subject, triples in subjects.items():
        # Use prefixed form if possible
        subject_str = _use_prefix(subject, mapping.namespaces)
        lines.append(f"{subject_str}")
        
        for i, triple in enumerate(triples):
            predicate = _use_prefix(triple.predicate, mapping.namespaces)
            object_str = _format_object(triple, mapping.namespaces)
            
            connector = "    " if i == 0 else "    ;"
            terminator = " ;" if i < len(triples) - 1 else " ."
            
            lines.append(f"{connector}{predicate} {object_str}{terminator}")
        lines.append("")
    
    return "\n".join(lines)

def _use_prefix(uri: str, namespaces: Dict[str, str]) -> str:
    """Convert full URI to prefixed form if possible"""
    for prefix, namespace in namespaces.items():
        if uri.startswith(namespace):
            local_name = uri[len(namespace):]
            return f"{prefix}:{local_name}"
    return f"<{uri}>"

def _format_object(triple: RDFTriple, namespaces: Dict[str, str]) -> str:
    """Format the object part of an RDF triple"""
    if triple.object_type == "uri":
        return _use_prefix(triple.object, namespaces)
    elif triple.object_type == "literal":
        # Escape quotes in literals
        escaped = triple.object.replace('"', '\\"')
        return f'"{escaped}"'
    elif triple.object_type == "typed_literal":
        escaped = triple.object.replace('"', '\\"')
        datatype = _use_prefix(triple.datatype, namespaces)
        return f'"{escaped}"^^{datatype}'
    else:
        return triple.object

if __name__ == "__main__":
    # Test ontology mapping
    from .gliner_extractor import ExtractedConcept, ConceptExtractionResult
    from .text_parser import DocumentMetadata, DocumentType
    
    # Sample data
    concepts = [
        ExtractedConcept("Raft", "algorithm", 10, 14, 0.9, "exploring Raft and PBFT"),
        ExtractedConcept("PBFT", "algorithm", 19, 23, 0.8, "exploring Raft and PBFT"),
        ExtractedConcept("Alice", "person_mention", 0, 5, 0.7, "Alice: I've been exploring")
    ]
    
    extraction_result = ConceptExtractionResult(
        concepts=concepts,
        domain_distribution={"cs": 2, "people": 1},
        concept_density=0.05,
        processing_metadata={}
    )
    
    doc_metadata = DocumentMetadata(
        DocumentType.CONVERSATION,
        0.8,
        {"line_count": 5, "has_speakers": True}
    )
    
    # Test mapping
    mapper = OntologyMapper()
    mapping = mapper.map_to_ontologies(
        "Sample content", extraction_result, doc_metadata
    )
    
    print(f"Generated {len(mapping.triples)} triples")
    print(f"Mapped {mapping.concepts_mapped} concepts")
    print("\nTurtle serialization:")
    print(serialize_triples_turtle(mapping))
