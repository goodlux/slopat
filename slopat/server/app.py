"""FastAPI web server for slop.at"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

from ..main import SlopProcessor
from ..parsers.gliner_extractor import ConceptExtractionResult
from ..parsers.text_parser import DocumentMetadata
from ..parsers.ontology_mapper import SemanticMapping

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="slop.at",
    description="Semantic web publishing platform - SLOP first, optimize later!",
    version="0.0.1"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # SvelteKit dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processor
SLOPS_DIR = Path.home() / ".slopat" / "slops"
SLOPS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize store in read-only mode for web server
from ..graph.store import SlopStore
read_only_store = SlopStore(read_only=True)
processor = SlopProcessor(output_dir=SLOPS_DIR, store=read_only_store)

# Request/Response models
class SlopSubmission(BaseModel):
    markdown: str
    title: Optional[str] = None

class SlopResponse(BaseModel):
    success: bool
    hash: str
    url: str
    title: str
    concepts_count: int
    message: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    """Index page listing all slops"""
    slop_files = sorted(SLOPS_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)

    slops_list = []
    for slop_file in slop_files[:50]:  # Show latest 50
        # Extract hash from filename
        hash_id = slop_file.stem
        # Read first line as title (hack for now)
        try:
            with open(slop_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract title from HTML
                title_start = content.find('<title>') + 7
                title_end = content.find(' - slop.at</title>')
                title = content[title_start:title_end] if title_start > 6 else hash_id
        except Exception:
            title = hash_id

        slops_list.append({
            'hash': hash_id,
            'title': title,
            'url': f'/{hash_id}'
        })

    # Generate simple index HTML
    slops_html = "\n".join([
        f'<li><a href="{s["url"]}" class="slop-link">{s["title"]}</a> <span class="hash">({s["hash"]})</span></li>'
        for s in slops_list
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>slop.at - Semantic Web Publishing</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .tagline {{
            font-size: 1.2rem;
            opacity: 0.9;
            margin-bottom: 3rem;
        }}
        .slops-list {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .slops-list h2 {{
            color: #333;
            margin-top: 0;
            margin-bottom: 1.5rem;
        }}
        .slops-list ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .slops-list li {{
            padding: 1rem;
            border-bottom: 1px solid #e5e7eb;
        }}
        .slops-list li:last-child {{
            border-bottom: none;
        }}
        .slop-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .slop-link:hover {{
            text-decoration: underline;
        }}
        .hash {{
            color: #6b7280;
            font-size: 0.85rem;
            font-family: monospace;
        }}
        .stats {{
            color: #333;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 2px solid #e5e7eb;
            font-size: 0.9rem;
        }}
        .empty-state {{
            color: #6b7280;
            text-align: center;
            padding: 3rem;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>slop.at</h1>
        <p class="tagline">Semantic web publishing platform - where ideas connect</p>

        <div class="slops-list">
            <h2>📚 Recent Slops</h2>
            {"<ul>" + slops_html + "</ul>" if slops_list else '<div class="empty-state">No slops yet! Submit your first one via the API or MCP server.</div>'}
            {"<div class='stats'>Total slops: " + str(len(slop_files)) + "</div>" if slop_files else ""}
        </div>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html)

@app.post("/slop", response_model=SlopResponse)
async def submit_slop(submission: SlopSubmission):
    """
    Submit markdown content and get back a unique hash URL
    """
    try:
        logger.info(f"Processing new slop submission (length: {len(submission.markdown)} chars)")

        # Process the markdown through the pipeline
        result = processor.process_content(
            submission.markdown,
            file_path=None,
            store_in_graph=True
        )

        # Extract hash from URL path
        hash_id = result.slop_page.url_path.lstrip('/')

        logger.info(f"Successfully created slop: {hash_id}")

        return SlopResponse(
            success=True,
            hash=hash_id,
            url=f"/{hash_id}",
            title=result.slop_page.title,
            concepts_count=len(result.slop_page.concepts),
            message="Slop successfully processed and stored!"
        )

    except Exception as e:
        logger.error(f"Error processing slop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{hash_id}", response_class=HTMLResponse)
async def get_slop(hash_id: str):
    """
    Retrieve a slop by its hash
    """
    # Clean hash_id to prevent directory traversal
    hash_id = hash_id.replace('/', '').replace('..', '')

    slop_path = SLOPS_DIR / f"{hash_id}.html"

    if not slop_path.exists():
        raise HTTPException(status_code=404, detail=f"Slop '{hash_id}' not found")

    try:
        with open(slop_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error reading slop {hash_id}: {e}")
        raise HTTPException(status_code=500, detail="Error reading slop")

@app.get("/api/slops")
async def list_slops():
    """List all slops for the frontend"""
    try:
        slop_files = sorted(SLOPS_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)

        slops_list = []
        for slop_file in slop_files:
            hash_id = slop_file.stem

            try:
                with open(slop_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract title
                title_start = content.find('<title>') + 7
                title_end = content.find(' - slop.at</title>')
                title = content[title_start:title_end] if title_start > 6 else hash_id

                # Count concepts
                import re
                concept_pattern = r'<span class="concept-[^"]+"'
                concepts_count = len(re.findall(concept_pattern, content))

                slops_list.append({
                    'hash': hash_id,
                    'title': title,
                    'url': f'/{hash_id}',
                    'concepts_count': concepts_count,
                    'modified': slop_file.stat().st_mtime
                })
            except Exception as e:
                logger.warning(f"Error reading slop {hash_id}: {e}")
                continue

        return JSONResponse({
            'slops': slops_list,
            'count': len(slops_list)
        })

    except Exception as e:
        logger.error(f"Error listing slops: {e}")
        raise HTTPException(status_code=500, detail="Error listing slops")

@app.get("/api/stats")
async def get_stats():
    """Get slop.at statistics"""
    stats = processor.get_statistics()
    slop_files = list(SLOPS_DIR.glob("*.html"))

    return JSONResponse({
        "total_slops": len(slop_files),
        "graph_stats": stats.get("graph_database", {}),
        "output_directory": str(SLOPS_DIR),
        "version": "0.0.1"
    })

@app.get("/api/slops/{hash_id}")
async def get_slop_json(hash_id: str):
    """
    Get slop data as JSON for the frontend
    """
    # Clean hash_id to prevent directory traversal
    hash_id = hash_id.replace('/', '').replace('..', '')

    slop_path = SLOPS_DIR / f"{hash_id}.html"

    if not slop_path.exists():
        raise HTTPException(status_code=404, detail=f"Slop '{hash_id}' not found")

    try:
        with open(slop_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Extract title from HTML
        title_start = html_content.find('<title>') + 7
        title_end = html_content.find(' - slop.at</title>')
        title = html_content[title_start:title_end] if title_start > 6 else "Untitled"

        # Extract just the main content (between <main> tags)
        import re
        main_pattern = r'<main class="main-content">(.*?)</main>'
        main_match = re.search(main_pattern, html_content, re.DOTALL)
        content_html = main_match.group(1) if main_match else html_content

        # Extract concepts from the HTML
        concepts = []
        concept_pattern = r'<span class="(concept-[^"]+)" data-concept="([^"]+)" data-domain="([^"]+)" data-confidence="([^"]+)" data-link-id="([^"]+)"'
        for match in re.finditer(concept_pattern, html_content):
            css_class, text, domain, confidence, link_id = match.groups()
            concepts.append({
                'text': text,
                'domain': domain,
                'confidence': float(confidence),
                'linkId': link_id
            })

        return JSONResponse({
            'hash': hash_id,
            'title': title,
            'html': content_html,  # Just the main content HTML fragment
            'concepts': concepts
        })

    except Exception as e:
        logger.error(f"Error reading slop {hash_id}: {e}")
        raise HTTPException(status_code=500, detail="Error reading slop")

@app.get("/api/concepts/{concept_text}/slops")
async def get_related_slops(concept_text: str):
    """
    Find all slops that mention a specific concept
    Uses the Oxigraph database to query semantic relationships
    """
    try:
        # Query Oxigraph for documents that mention this concept
        # Use the store's built-in method
        related_docs = processor.store.find_related_documents(concept_text, limit=20)

        results = []
        for doc in related_docs:
            # Extract hash from document URI if available
            doc_uri = doc.get('doc', '')
            hash_id = None
            if 'slop-' in doc_uri:
                # Extract hash from URI like http://slop.at/docs/slop-856e7bb8
                hash_id = doc_uri.split('slop-')[-1].rstrip('>')

            results.append({
                'hash': hash_id,
                'title': doc.get('title', 'Untitled'),
                'url': f"/{hash_id}" if hash_id else None,
                'confidence': doc.get('confidence'),
                'domain': doc.get('domain')
            })

        return JSONResponse({
            'concept': concept_text,
            'related_slops': results,
            'count': len(results)
        })

    except Exception as e:
        logger.error(f"Error querying related slops for '{concept_text}': {e}")
        # Return empty results instead of error to avoid breaking frontend
        return JSONResponse({
            'concept': concept_text,
            'related_slops': [],
            'count': 0,
            'error': str(e)
        })

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "slop.at", "version": "0.0.1"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
