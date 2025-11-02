"""Text parsing and document type detection for slop.at"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class DocumentType(Enum):
    CONVERSATION = "conversation"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    STRUCTURED = "structured"
    RANDOM = "random"

@dataclass
class DocumentMetadata:
    doc_type: DocumentType
    confidence: float
    features: Dict[str, any]
    suggested_title: Optional[str] = None

class TextParser:
    """
    Detect document type and extract basic structure.
    Based on patterns learned from CodeDoc's AST parsing approach.
    """
    
    def __init__(self):
        self.conversation_patterns = [
            r'^[A-Z][a-z]+:',  # "Alice:"
            r'^[a-zA-Z0-9_-]+:',  # "user123:"
            r'^\*\*[^*]+\*\*:',  # "**Assistant**:"
            r'^>\s',  # "> quoted text"
        ]
        
        self.markdown_patterns = [
            r'^#{1,6}\s',  # Headers
            r'^\*\s',  # Lists
            r'^\d+\.\s',  # Numbered lists
            r'^\[.*\]\(.*\)',  # Links
            r'`[^`]+`',  # Inline code
            r'^```',  # Code blocks
        ]
        
        self.structured_patterns = [
            r'^\d+\.',  # Numbered items
            r'^[A-Z][A-Z\s]+:',  # "SECTION HEADER:"
            r'^-{3,}',  # Horizontal rules
            r'^\|',  # Tables
        ]
    
    def classify_document(self, content: str) -> DocumentMetadata:
        """Alias for detect_document_type to match main.py interface"""
        return self.detect_document_type(content)
    
    def detect_document_type(self, content: str) -> DocumentMetadata:
        """
        Detect the type of document based on content patterns.
        Similar to how we detect function types in CodeDoc AST parsing.
        """
        lines = content.strip().split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return DocumentMetadata(DocumentType.RANDOM, 0.0, {})
        
        # Count pattern matches
        conversation_score = self._count_patterns(lines, self.conversation_patterns)
        markdown_score = self._count_patterns(lines, self.markdown_patterns)
        structured_score = self._count_patterns(lines, self.structured_patterns)
        
        # Calculate confidence scores
        conv_confidence = conversation_score / total_lines
        md_confidence = markdown_score / total_lines  
        struct_confidence = structured_score / total_lines
        
        # Determine type based on highest confidence
        scores = [
            (DocumentType.CONVERSATION, conv_confidence),
            (DocumentType.MARKDOWN, md_confidence),
            (DocumentType.STRUCTURED, struct_confidence),
        ]
        
        doc_type, confidence = max(scores, key=lambda x: x[1])
        
        # Default to plain text if confidence is too low
        if confidence < 0.1:
            doc_type = DocumentType.PLAIN_TEXT
            confidence = 0.5
        
        # Extract features for downstream processing
        features = {
            'line_count': total_lines,
            'avg_line_length': sum(len(line) for line in lines) / total_lines,
            'conversation_markers': conversation_score,
            'markdown_markers': markdown_score,
            'structured_markers': structured_score,
            'has_headers': any(line.startswith('#') for line in lines),
            'has_speakers': any(':' in line[:50] for line in lines[:10]),
        }
        
        # Generate suggested title
        title = self._extract_title(lines, doc_type)
        
        return DocumentMetadata(doc_type, confidence, features, title)
    
    def _count_patterns(self, lines: List[str], patterns: List[str]) -> int:
        """Count how many lines match any of the given patterns."""
        count = 0
        for line in lines:
            if any(re.search(pattern, line) for pattern in patterns):
                count += 1
        return count
    
    def _extract_title(self, lines: List[str], doc_type: DocumentType) -> Optional[str]:
        """Extract a suggested title based on document type."""
        if not lines:
            return None
            
        # For markdown, look for first header
        if doc_type == DocumentType.MARKDOWN:
            for line in lines[:5]:
                if line.startswith('#'):
                    return line.lstrip('#').strip()
        
        # For conversations, use first few words of first substantial line
        if doc_type == DocumentType.CONVERSATION:
            for line in lines[:5]:
                if len(line.strip()) > 10 and ':' not in line[:50]:
                    words = line.strip().split()[:6]
                    return ' '.join(words) + ('...' if len(words) == 6 else '')
        
        # Default: first substantial line
        for line in lines[:3]:
            if len(line.strip()) > 10:
                words = line.strip().split()[:6]
                return ' '.join(words) + ('...' if len(words) == 6 else '')
        
        return None

def parse_text_file(file_path: Path) -> Tuple[str, DocumentMetadata]:
    """
    Parse a text file and return content + metadata.
    Main entry point similar to CodeDoc's parse_file().
    """
    parser = TextParser()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = parser.detect_document_type(content)
    
    return content, metadata

if __name__ == "__main__":
    # Test with some sample text
    sample_markdown = """# My Project
    
This is a **bold** statement about AI.

- First item
- Second item

```python
def hello():
    print("world")
```
"""
    
    sample_conversation = """Alice: Hey, what do you think about distributed systems?

Bob: Well, I think consensus algorithms are really fascinating. Have you looked into Raft?

Alice: Yeah! The leader election process is elegant. But what about Byzantine fault tolerance?

Bob: That's where things get complex. PBFT is the classic algorithm, but it has some limitations...
"""
    
    parser = TextParser()
    
    print("Markdown example:")
    md_result = parser.detect_document_type(sample_markdown)
    print(f"Type: {md_result.doc_type}, Confidence: {md_result.confidence:.2f}")
    print(f"Title: {md_result.suggested_title}")
    print()
    
    print("Conversation example:")
    conv_result = parser.detect_document_type(sample_conversation) 
    print(f"Type: {conv_result.doc_type}, Confidence: {conv_result.confidence:.2f}")
    print(f"Title: {conv_result.suggested_title}")
