"""Oxigraph wrapper for slop.at semantic storage"""

from typing import List, Dict, Optional, Iterator, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

try:
    import pyoxigraph as ox
except ImportError:
    print("Pyoxigraph not installed. Install with: pip install pyoxigraph")
    ox = None

from ..parsers.ontology_mapper import SemanticMapping, RDFTriple

@dataclass
class QueryResult:
    """Results from SPARQL queries"""
    bindings: List[Dict[str, str]]
    total_results: int
    query_time_ms: Optional[float] = None

class SlopStore:
    """
    Oxigraph-based storage for slop.at semantic data.
    Inspired by CodeDoc's graph storage patterns.
    """
    
    def __init__(self, data_dir: Path = None, read_only: bool = False):
        """Initialize Oxigraph store

        Args:
            data_dir: Directory for storing RDF data
            read_only: If True, open store in read-only mode (won't acquire lock)
        """
        if ox is None:
            raise ImportError("Pyoxigraph is required for semantic storage")

        # Default data directory
        if data_dir is None:
            data_dir = Path.home() / ".slopat" / "data"

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.read_only = read_only

        # Initialize Oxigraph store
        store_path = self.data_dir / "oxigraph"
        if read_only:
            # Open in read-only mode using Store.read_only
            self.store = ox.Store.read_only(str(store_path))
        else:
            self.store = ox.Store(str(store_path))

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize core ontologies if store is empty (only in read-write mode)
        if not read_only:
            self._initialize_core_ontologies()
    
    def _initialize_core_ontologies(self):
        """Load core slop.at ontologies if not already present"""
        # Check if we have any data
        count_query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
        result = self.query_sparql(count_query)
        
        if result.bindings and int(result.bindings[0].get('count', 0)) == 0:
            self.logger.info("Initializing core ontologies...")
            self._load_core_ontology()
    
    def _load_core_ontology(self):
        """Load the core slop.at ontology definitions"""
        core_ontology = """
@prefix slop: <http://slop.at/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

# Core Classes
slop:Document a owl:Class ;
    rdfs:label "Document" ;
    rdfs:comment "A document or conversation in slop.at" .

slop:ConversationDocument a owl:Class ;
    rdfs:subClassOf slop:Document ;
    rdfs:label "Conversation Document" .

slop:MarkdownDocument a owl:Class ;
    rdfs:subClassOf slop:Document ;
    rdfs:label "Markdown Document" .

slop:PlainTextDocument a owl:Class ;
    rdfs:subClassOf slop:Document ;
    rdfs:label "Plain Text Document" .

slop:StructuredDocument a owl:Class ;
    rdfs:subClassOf slop:Document ;
    rdfs:label "Structured Document" .

slop:Concept a owl:Class ;
    rdfs:label "Concept" ;
    rdfs:comment "A concept extracted from a document" .

# Core Properties
slop:discusses a owl:ObjectProperty ;
    rdfs:domain slop:Document ;
    rdfs:range slop:Concept ;
    rdfs:label "discusses" .

slop:coOccursWith a owl:ObjectProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range slop:Concept ;
    rdfs:label "co-occurs with" .

slop:typeConfidence a owl:DatatypeProperty ;
    rdfs:domain slop:Document ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#float> ;
    rdfs:label "type confidence" .

slop:confidence a owl:DatatypeProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#float> ;
    rdfs:label "confidence" .

slop:glinerLabel a owl:DatatypeProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> ;
    rdfs:label "GLiNER label" .

slop:context a owl:DatatypeProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> ;
    rdfs:label "context" .

slop:startPosition a owl:DatatypeProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#integer> ;
    rdfs:label "start position" .

slop:endPosition a owl:DatatypeProperty ;
    rdfs:domain slop:Concept ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#integer> ;
    rdfs:label "end position" .

slop:primaryDomain a owl:DatatypeProperty ;
    rdfs:domain slop:Document ;
    rdfs:range <http://www.w3.org/2001/XMLSchema#string> ;
    rdfs:label "primary domain" .
"""
        
        # Load into store
        self.store.load(
            core_ontology.encode('utf-8'),
            mime_type="text/turtle"
        )
        
        self.logger.info("Core ontology loaded successfully")
    
    def store_semantic_mapping(self, mapping: SemanticMapping, graph_uri: Optional[str] = None) -> bool:
        """
        Store a semantic mapping in the graph database.
        Similar to CodeDoc's graph storage methods.
        """
        try:
            # Convert triples to Oxigraph format
            ox_triples = []
            for triple in mapping.triples:
                ox_triple = self._convert_to_oxigraph_triple(triple, mapping.namespaces)
                if ox_triple:
                    ox_triples.append(ox_triple)
            
            # Insert triples
            if graph_uri:
                graph = ox.NamedNode(graph_uri)
                quads = [ox.Quad(t.subject, t.predicate, t.object, graph) for t in ox_triples]
                self.store.extend(quads)
            else:
                self.store.extend(ox_triples)
            
            self.logger.info(f"Stored {len(ox_triples)} triples from semantic mapping")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing semantic mapping: {e}")
            return False
    
    def _convert_to_oxigraph_triple(self, triple: RDFTriple, namespaces: Dict[str, str]) -> Optional[ox.Triple]:
        """Convert our RDF triple format to Oxigraph triple"""
        try:
            # Subject (always URI)
            subject = self._expand_uri(triple.subject, namespaces)
            ox_subject = ox.NamedNode(subject)
            
            # Predicate (always URI)
            predicate = self._expand_uri(triple.predicate, namespaces)
            ox_predicate = ox.NamedNode(predicate)
            
            # Object (URI, literal, or typed literal)
            if triple.object_type == "uri":
                object_uri = self._expand_uri(triple.object, namespaces)
                ox_object = ox.NamedNode(object_uri)
            elif triple.object_type == "literal":
                ox_object = ox.Literal(triple.object)
            elif triple.object_type == "typed_literal":
                datatype_uri = self._expand_uri(triple.datatype, namespaces)
                ox_object = ox.Literal(triple.object, datatype=ox.NamedNode(datatype_uri))
            else:
                self.logger.warning(f"Unknown object type: {triple.object_type}")
                return None
            
            return ox.Triple(ox_subject, ox_predicate, ox_object)
            
        except Exception as e:
            self.logger.error(f"Error converting triple: {e}")
            return None
    
    def _expand_uri(self, uri: str, namespaces: Dict[str, str]) -> str:
        """Expand prefixed URI to full URI"""
        if ":" in uri and not uri.startswith("http"):
            prefix, local_name = uri.split(":", 1)
            if prefix in namespaces:
                return namespaces[prefix] + local_name
        return uri
    
    def query_sparql(self, query: str, timeout_seconds: int = 30) -> QueryResult:
        """
        Execute SPARQL query and return results.
        Main query interface similar to CodeDoc's query methods.
        """
        try:
            import time
            start_time = time.time()
            
            # Execute query
            results = self.store.query(query)
            
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Convert results to our format
            bindings = []
            for solution in results:
                binding = {}
                # pyoxigraph QuerySolution is a dict-like object
                # Iterate through keys (variable names)
                if hasattr(solution, '__iter__'):
                    # Try iterating as a mapping
                    try:
                        for var_name in solution:
                            value = solution[var_name]
                            if value is not None:
                                if isinstance(value, ox.NamedNode):
                                    binding[var_name] = str(value.value)
                                elif isinstance(value, ox.Literal):
                                    binding[var_name] = str(value.value)
                                else:
                                    binding[var_name] = str(value)
                    except Exception as e:
                        self.logger.warning(f"Error iterating solution: {e}")
                        continue
                bindings.append(binding)
            
            return QueryResult(
                bindings=bindings,
                total_results=len(bindings),
                query_time_ms=query_time
            )
            
        except Exception as e:
            self.logger.error(f"SPARQL query error: {e}")
            return QueryResult(bindings=[], total_results=0)
    
    def find_related_documents(self, concept_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Find documents related to a specific concept.
        Used for sidebar updates when users click concept links.
        """
        query = f"""
        PREFIX slop: <http://slop.at/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dct: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?doc ?title ?confidence ?domain WHERE {{
            ?concept rdfs:label "{concept_text}" .
            ?doc slop:discusses ?concept .
            OPTIONAL {{ ?doc dct:title ?title }}
            OPTIONAL {{ ?doc slop:typeConfidence ?confidence }}
            OPTIONAL {{ ?doc slop:primaryDomain ?domain }}
        }}
        ORDER BY DESC(?confidence)
        LIMIT {limit}
        """
        
        result = self.query_sparql(query)
        return result.bindings
    
    def find_co_occurring_concepts(self, concept_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Find concepts that frequently co-occur with the given concept.
        """
        query = f"""
        PREFIX slop: <http://slop.at/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?related_concept (COUNT(?doc) as ?frequency) WHERE {{
            ?concept rdfs:label "{concept_text}" .
            ?concept slop:coOccursWith ?related .
            ?related rdfs:label ?related_concept .
            ?doc slop:discusses ?concept .
            ?doc slop:discusses ?related .
        }}
        GROUP BY ?related_concept
        ORDER BY DESC(?frequency)
        LIMIT {limit}
        """
        
        result = self.query_sparql(query)
        return result.bindings
    
    def get_document_stats(self) -> Dict[str, int]:
        """Get overall statistics about stored documents"""
        queries = {
            "total_documents": "SELECT (COUNT(DISTINCT ?doc) as ?count) WHERE { ?doc a slop:Document }",
            "total_concepts": "SELECT (COUNT(DISTINCT ?concept) as ?count) WHERE { ?concept a slop:Concept }",
            "conversations": "SELECT (COUNT(?doc) as ?count) WHERE { ?doc a slop:ConversationDocument }",
            "markdown_docs": "SELECT (COUNT(?doc) as ?count) WHERE { ?doc a slop:MarkdownDocument }",
        }
        
        stats = {}
        for stat_name, query in queries.items():
            result = self.query_sparql(query)
            if result.bindings:
                stats[stat_name] = int(result.bindings[0].get('count', 0))
            else:
                stats[stat_name] = 0
        
        return stats
    
    def export_document_turtle(self, doc_uri: str) -> Optional[str]:
        """Export a specific document and its concepts as Turtle"""
        query = f"""
        CONSTRUCT {{
            <{doc_uri}> ?p ?o .
            ?concept ?cp ?co .
        }}
        WHERE {{
            <{doc_uri}> ?p ?o .
            OPTIONAL {{
                <{doc_uri}> slop:discusses ?concept .
                ?concept ?cp ?co .
            }}
        }}
        """
        
        try:
            results = self.store.query(query)
            return results.serialize(format="text/turtle")
        except Exception as e:
            self.logger.error(f"Error exporting document: {e}")
            return None
    
    def clear_all_data(self) -> bool:
        """Clear all data from the store (for testing/reset)"""
        try:
            self.store.clear()
            self._load_core_ontology()  # Reload core ontology
            return True
        except Exception as e:
            self.logger.error(f"Error clearing store: {e}")
            return False

# Convenience functions
def get_default_store() -> SlopStore:
    """Get the default slop.at store instance"""
    return SlopStore()

if __name__ == "__main__":
    # Test store functionality
    store = SlopStore()
    
    # Test basic query
    stats = store.get_document_stats()
    print("Store statistics:", stats)
    
    # Test SPARQL query
    query = """
    PREFIX slop: <http://slop.at/ontology#>
    SELECT ?class WHERE {
        ?class a <http://www.w3.org/2002/07/owl#Class> .
    }
    """
    
    result = store.query_sparql(query)
    print(f"Found {result.total_results} classes in ontology")
    for binding in result.bindings:
        print(f"  {binding}")
