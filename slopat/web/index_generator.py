"""Generate an index page for slop.at documents"""

from pathlib import Path
from typing import List
import html

def generate_index_page(output_dir: Path) -> str:
    """Generate an index.html page listing all slop documents"""
    
    html_files = list(output_dir.glob("*.html"))
    html_files = [f for f in html_files if f.name != "index.html"]  # Exclude self
    
    # Sort by modification time (newest first)
    html_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    # Read basic info from each file
    slops = []
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8')
            
            # Extract title from HTML
            title_start = content.find('<title>')
            title_end = content.find('</title>')
            if title_start != -1 and title_end != -1:
                title = content[title_start + 7:title_end].replace(' - slop.at', '')
            else:
                title = html_file.stem.replace('-', ' ').replace('_', ' ').title()
            
            # Extract concept count from subtitle
            concept_count = "Unknown"
            subtitle_start = content.find('<div class="subtitle">')
            if subtitle_start != -1:
                subtitle_end = content.find('</div>', subtitle_start)
                subtitle = content[subtitle_start:subtitle_end]
                if 'concepts' in subtitle:
                    # Extract number before "concepts"
                    import re
                    match = re.search(r'(\d+)\s+concepts', subtitle)
                    if match:
                        concept_count = match.group(1)
            
            slops.append({
                'filename': html_file.name,
                'title': title,
                'concept_count': concept_count,
                'size': f"{html_file.stat().st_size // 1024}KB"
            })
        except Exception:
            # Fallback for files we can't parse
            slops.append({
                'filename': html_file.name,
                'title': html_file.stem.replace('-', ' ').replace('_', ' ').title(),
                'concept_count': "Unknown",
                'size': f"{html_file.stat().st_size // 1024}KB"
            })
    
    # Generate HTML
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>slop.at - Semantic Document Explorer</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin: 0;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            margin-top: 1rem;
            opacity: 0.9;
        }}
        
        .stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 3rem;
            flex-wrap: wrap;
        }}
        
        .stat {{
            background: rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            display: block;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }}
        
        .slops-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }}
        
        .slop-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.2);
        }}
        
        .slop-card:hover {{
            transform: translateY(-5px);
            background: rgba(255,255,255,0.15);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .slop-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: white;
            text-decoration: none;
            display: block;
        }}
        
        .slop-title:hover {{
            color: #ffd700;
        }}
        
        .slop-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .concept-badge {{
            background: rgba(255,215,0,0.2);
            color: #ffd700;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            opacity: 0.7;
        }}
        
        .empty-state h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        .command {{
            background: rgba(0,0,0,0.3);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-family: 'Monaco', 'Courier New', monospace;
            margin: 1rem 0;
            display: inline-block;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .stats {{
                gap: 1rem;
            }}
            
            .slops-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>slop.at</h1>
            <p>Semantic Document Explorer</p>
        </header>
        
        <div class="stats">
            <div class="stat">
                <span class="stat-number">{len(slops)}</span>
                <div class="stat-label">Documents</div>
            </div>
            <div class="stat">
                <span class="stat-number">{sum(int(s['concept_count']) for s in slops if s['concept_count'].isdigit())}</span>
                <div class="stat-label">Total Concepts</div>
            </div>
            <div class="stat">
                <span class="stat-number">{sum(int(s['size'].replace('KB', '')) for s in slops)}</span>
                <div class="stat-label">KB Generated</div>
            </div>
        </div>
"""
    
    if slops:
        index_html += """
        <div class="slops-grid">
"""
        for slop in slops:
            index_html += f"""
            <div class="slop-card">
                <a href="{html.escape(slop['filename'])}" class="slop-title">
                    {html.escape(slop['title'])}
                </a>
                <div class="slop-meta">
                    <span class="concept-badge">{slop['concept_count']} concepts</span>
                    <span>{slop['size']}</span>
                </div>
            </div>
"""
        index_html += """
        </div>
"""
    else:
        index_html += """
        <div class="empty-state">
            <h2>No slops yet!</h2>
            <p>Process some documents to get started:</p>
            <div class="command">uv run slopat process data/</div>
        </div>
"""
    
    index_html += """
    </div>
</body>
</html>"""
    
    return index_html

def create_index_page(output_dir: Path) -> Path:
    """Create an index.html file in the output directory"""
    index_html = generate_index_page(output_dir)
    index_path = output_dir / "index.html"
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    return index_path
