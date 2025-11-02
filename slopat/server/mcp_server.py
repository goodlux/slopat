"""MCP server for slop.at - allows Claude Desktop to submit slops"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

from ..main import SlopProcessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize processor
SLOPS_DIR = Path.home() / ".slopat" / "slops"
SLOPS_DIR.mkdir(parents=True, exist_ok=True)

processor = SlopProcessor(output_dir=SLOPS_DIR)

# Create MCP server
app = Server("slopat")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="submit_slop",
            description="Submit markdown content to slop.at and get back a semantic HTML page with concept extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "The markdown content to process and publish"
                    },
                    "title": {
                        "type": "string",
                        "description": "Optional title for the slop"
                    }
                },
                "required": ["markdown"]
            }
        ),
        Tool(
            name="list_slops",
            description="List all published slops with their hashes and titles",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of slops to return (default: 20)",
                        "default": 20
                    }
                }
            }
        ),
        Tool(
            name="get_slop_stats",
            description="Get statistics about the slop.at instance",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls from Claude"""

    if name == "submit_slop":
        markdown = arguments.get("markdown", "")
        title = arguments.get("title")

        if not markdown:
            return [TextContent(
                type="text",
                text="Error: No markdown content provided"
            )]

        try:
            logger.info(f"Processing slop submission via MCP (length: {len(markdown)} chars)")

            # Process the markdown
            result = processor.process_content(
                markdown,
                file_path=None,
                store_in_graph=True
            )

            # Extract hash from URL path
            hash_id = result.slop_page.url_path.lstrip('/')

            # Build response
            response = f"""✅ Slop successfully created!

**Hash:** `{hash_id}`
**Title:** {result.slop_page.title}
**Concepts Extracted:** {len(result.slop_page.concepts)}
**URL:** http://localhost:8000/{hash_id}

**Top Concepts:**
"""
            # Add top concepts by domain
            concepts_by_domain = {}
            for concept in result.slop_page.concepts:
                domain = concept.label
                if domain not in concepts_by_domain:
                    concepts_by_domain[domain] = []
                concepts_by_domain[domain].append(concept)

            for domain, concepts in list(concepts_by_domain.items())[:5]:
                top_concepts = sorted(concepts, key=lambda x: x.confidence, reverse=True)[:3]
                response += f"\n- **{domain}:** {', '.join([c.text for c in top_concepts])}"

            response += f"\n\n**Saved to:** {result.saved_path}"

            logger.info(f"Successfully created slop: {hash_id}")

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error processing slop: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error processing slop: {str(e)}"
            )]

    elif name == "list_slops":
        limit = arguments.get("limit", 20)

        try:
            slop_files = sorted(SLOPS_DIR.glob("*.html"), key=lambda x: x.stat().st_mtime, reverse=True)
            slop_files = slop_files[:limit]

            if not slop_files:
                return [TextContent(
                    type="text",
                    text="No slops found. Submit your first one with `submit_slop`!"
                )]

            response = f"📚 **Recent Slops** (showing {len(slop_files)} of {len(list(SLOPS_DIR.glob('*.html')))} total)\n\n"

            for slop_file in slop_files:
                hash_id = slop_file.stem
                # Try to extract title from HTML
                try:
                    with open(slop_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        title_start = content.find('<title>') + 7
                        title_end = content.find(' - slop.at</title>')
                        title = content[title_start:title_end] if title_start > 6 else hash_id
                except Exception:
                    title = hash_id

                response += f"- **{title}** (`{hash_id}`)\n  URL: http://localhost:8000/{hash_id}\n\n"

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error listing slops: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error listing slops: {str(e)}"
            )]

    elif name == "get_slop_stats":
        try:
            stats = processor.get_statistics()
            slop_files = list(SLOPS_DIR.glob("*.html"))

            response = f"""📊 **slop.at Statistics**

**Total Slops:** {len(slop_files)}
**Output Directory:** {SLOPS_DIR}

**Graph Database:**
"""
            for key, value in stats.get("graph_database", {}).items():
                response += f"- {key.replace('_', ' ').title()}: {value}\n"

            response += "\n**Components:**\n"
            for component, loaded in stats.get("components_loaded", {}).items():
                status = "✅" if loaded else "❌"
                response += f"{status} {component.replace('_', ' ').title()}\n"

            return [TextContent(type="text", text=response)]

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return [TextContent(
                type="text",
                text=f"❌ Error getting stats: {str(e)}"
            )]

    else:
        return [TextContent(
            type="text",
            text=f"❌ Unknown tool: {name}"
        )]

async def main():
    """Run the MCP server"""
    logger.info("Starting slop.at MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
