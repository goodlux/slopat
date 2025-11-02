"""Main slop.at processing pipeline"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from dataclasses import dataclass

from .parsers.text_parser import TextParser, DocumentMetadata
from .parsers.gliner_extractor import ConceptExtractor, ConceptExtractionResult
from .parsers.ontology_mapper import OntologyMapper, SemanticMapping
from .graph.store import SlopStore
from .web.html_generator import HTMLGenerator, SlopPage, save_slop_page

@dataclass
class ProcessingResult:
    """Complete result of processing a slop"""
    slop_page: SlopPage
    extraction_result: ConceptExtractionResult
    semantic_mapping: SemanticMapping
    doc_metadata: DocumentMetadata
    saved_path: Optional[Path] = None
    graph_stored: bool = False

class SlopProcessor:
    """
    Main processor that orchestrates the complete slop.at pipeline.
    Similar to CodeDoc's main processing architecture.
    """
    
    def __init__(
        self,
        output_dir: Path = None,
        store: Optional[SlopStore] = None,
        gliner_model: str = "urchade/gliner_base"
    ):
        # Set up directories
        if output_dir is None:
            output_dir = Path.home() / ".slopat" / "output"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.text_parser = TextParser()
        self.concept_extractor = ConceptExtractor(gliner_model)
        self.ontology_mapper = OntologyMapper()
        self.html_generator = HTMLGenerator()
        
        # Initialize graph store
        if store is None:
            store = SlopStore()
        self.store = store
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    def process_file(self, file_path: Path) -> ProcessingResult:
        """
        Process a text file through the complete slop.at pipeline.
        Main entry point for file-based processing.
        """
        self.logger.info(f"Processing file: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.process_content(content, file_path=file_path)
    
    def process_content(
        self, 
        content: str, 
        file_path: Optional[Path] = None,
        store_in_graph: bool = True
    ) -> ProcessingResult:
        """
        Process text content through the complete slop.at pipeline.
        Core processing method inspired by CodeDoc's analysis flow.
        """
        try:
            # Step 1: Document classification and parsing
            self.logger.info("Step 1: Analyzing document structure...")
            doc_metadata = self.text_parser.classify_document(content)
            self.logger.info(f"Detected document type: {doc_metadata.doc_type} (confidence: {doc_metadata.confidence:.2f})")
            
            # Step 2: Concept extraction with GLiNER
            self.logger.info("Step 2: Extracting concepts with GLiNER...")
            extraction_result = self.concept_extractor.extract_concepts(content)
            self.logger.info(f"Extracted {len(extraction_result.concepts)} concepts across {len(extraction_result.domain_distribution)} domains")
            
            # Step 3: Ontology mapping and RDF generation
            self.logger.info("Step 3: Mapping to ontologies and generating RDF...")
            semantic_mapping = self.ontology_mapper.map_to_ontologies(
                content, extraction_result, doc_metadata, file_path
            )
            self.logger.info(f"Generated {len(semantic_mapping.triples)} RDF triples")
            
            # Step 4: Store in graph database
            graph_stored = False
            if store_in_graph:
                self.logger.info("Step 4: Storing in graph database...")
                graph_stored = self.store.store_semantic_mapping(semantic_mapping)
                self.logger.info(f"Graph storage: {'success' if graph_stored else 'failed'}")
            
            # Step 5: Generate beautiful HTML
            self.logger.info("Step 5: Generating HTML page...")
            slop_page = self.html_generator.generate_slop_page(
                content, extraction_result, doc_metadata, semantic_mapping, file_path
            )
            self.logger.info(f"Generated HTML page: {slop_page.title}")
            
            # Step 6: Save HTML to disk
            self.logger.info("Step 6: Saving HTML page...")
            saved_path = save_slop_page(slop_page, self.output_dir)
            self.logger.info(f"Saved page to: {saved_path}")
            
            return ProcessingResult(
                slop_page=slop_page,
                extraction_result=extraction_result,
                semantic_mapping=semantic_mapping,
                doc_metadata=doc_metadata,
                saved_path=saved_path,
                graph_stored=graph_stored
            )
            
        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            raise
    
    def batch_process(self, input_dir: Path, pattern: str = "*.txt") -> List[ProcessingResult]:
        """Process multiple files in a directory"""
        self.logger.info(f"Batch processing files in {input_dir} matching {pattern}")
        
        results = []
        files = list(input_dir.glob(pattern))
        
        for i, file_path in enumerate(files):
            self.logger.info(f"Processing file {i+1}/{len(files)}: {file_path.name}")
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                continue
        
        self.logger.info(f"Batch processing complete: {len(results)}/{len(files)} files processed successfully")
        return results
    
    def find_related_slops(self, concept_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """Find slops related to a specific concept"""
        return self.store.find_related_documents(concept_text, limit)
    
    def find_co_occurring_concepts(self, concept_text: str, limit: int = 10) -> List[Dict[str, str]]:
        """Find concepts that co-occur with the given concept"""
        return self.store.find_co_occurring_concepts(concept_text, limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall processing statistics"""
        graph_stats = self.store.get_document_stats()
        
        # Add file system stats
        html_files = list(self.output_dir.glob("*.html"))
        
        return {
            "graph_database": graph_stats,
            "html_files": len(html_files),
            "output_directory": str(self.output_dir),
            "components_loaded": {
                "text_parser": True,
                "concept_extractor": hasattr(self.concept_extractor, 'model'),
                "ontology_mapper": True,
                "html_generator": True,
                "graph_store": True
            }
        }
    
    def export_document_turtle(self, slop_url: str) -> Optional[str]:
        """Export a specific slop as RDF Turtle"""
        # Convert URL path to document URI
        doc_uri = f"http://slop.at/ontology#document/{slop_url.lstrip('/')}"
        return self.store.export_document_turtle(doc_uri)

# Convenience functions for simple usage
def process_file_simple(file_path: Path, output_dir: Path = None) -> ProcessingResult:
    """Simple file processing without persistence"""
    processor = SlopProcessor(output_dir=output_dir)
    return processor.process_file(file_path)

def process_text_simple(content: str, output_dir: Path = None) -> ProcessingResult:
    """Simple text processing without persistence"""
    processor = SlopProcessor(output_dir=output_dir)
    return processor.process_content(content)

def main():
    """Main CLI entry point for slop.at"""
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track
    
    console = Console()
    
    @click.group(invoke_without_command=True)
    @click.pass_context
    @click.version_option(version="0.1.0")
    def cli(ctx):
        """slop.at - Semantic document analysis with beautiful HTML generation"""
        if ctx.invoked_subcommand is None:
            console.print("[yellow]No command specified. Use --help to see available commands.[/yellow]")
            console.print("[dim]Quick start: slopat process data/sample_conversation.txt[/dim]")
    
    @cli.command()
    @click.argument('input_path', type=click.Path(exists=True))
    @click.option('--output', '-o', type=click.Path(), help='Output directory')
    @click.option('--no-graph', is_flag=True, help='Skip graph database storage')
    def process(input_path, output, no_graph):
        """Process a single file or directory of files"""
        input_path = Path(input_path)
        output_dir = Path(output) if output else None
        
        processor = SlopProcessor(output_dir=output_dir)
        
        if input_path.is_file():
            console.print(f"[blue]Processing:[/blue] {input_path}")
            
            try:
                result = processor.process_content(
                    input_path.read_text(encoding='utf-8'),
                    file_path=input_path,
                    store_in_graph=not no_graph
                )
                
                console.print(f"[green]✓ Success![/green] Generated: {result.slop_page.title}")
                console.print(f"[dim]URL:[/dim] {result.slop_page.url_path}")
                console.print(f"[dim]Concepts:[/dim] {len(result.slop_page.concepts)}")
                console.print(f"[dim]Saved to:[/dim] {result.saved_path}")
                
                if result.extraction_result.concepts:
                    console.print("\n[bold]Top concepts:[/bold]")
                    for concept in result.extraction_result.concepts[:5]:
                        console.print(f"  • {concept.text} ([cyan]{concept.label}[/cyan]) - {concept.confidence:.2f}")
                        
            except Exception as e:
                console.print(f"[red]✗ Error:[/red] {e}")
                raise click.Abort()
                
        elif input_path.is_dir():
            files = list(input_path.glob("*.md"))
            
            if not files:
                console.print(f"[yellow]No .md files found in {input_path}[/yellow]")
                console.print("[dim]Focusing on markdown files for structured browsing[/dim]")
                return
                
            console.print(f"[blue]Batch processing {len(files)} files...[/blue]")
            
            results = []
            for file_path in track(files, description="Processing..."):
                try:
                    result = processor.process_file(file_path)
                    results.append(result)
                except Exception as e:
                    console.print(f"[red]Failed to process {file_path}: {e}[/red]")
            
            console.print(f"\n[green]✓ Processed {len(results)}/{len(files)} files successfully[/green]")
            
            # Show results table
            table = Table(title="Processing Results")
            table.add_column("File", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Concepts", justify="right")
            
            for result in results:
                file_name = result.saved_path.name if result.saved_path else "N/A"
                table.add_row(
                    file_name,
                    result.slop_page.title,
                    str(len(result.slop_page.concepts))
                )
            
            console.print(table)
    
    @cli.command()
    @click.option('--output', '-o', type=click.Path(), help='Output directory')
    def stats(output):
        """Show processing statistics"""
        output_dir = Path(output) if output else None
        processor = SlopProcessor(output_dir=output_dir)
        
        stats = processor.get_statistics()
        
        console.print("\n[bold blue]slop.at Statistics[/bold blue]")
        
        # Graph database stats
        table = Table(title="Graph Database")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")
        
        for key, value in stats["graph_database"].items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(table)
        
        # Component status
        console.print("\n[bold]Component Status:[/bold]")
        for component, loaded in stats["components_loaded"].items():
            status = "[green]✓[/green]" if loaded else "[red]✗[/red]"
            console.print(f"  {status} {component.replace('_', ' ').title()}")
        
        console.print(f"\n[dim]HTML Files: {stats['html_files']}[/dim]")
        console.print(f"[dim]Output Directory: {stats['output_directory']}[/dim]")
    
    @cli.command()
    @click.argument('concept_text')
    @click.option('--limit', '-l', default=10, help='Number of results to show')
    def related(concept_text, limit):
        """Find documents related to a concept"""
        processor = SlopProcessor()
        
        console.print(f"[blue]Searching for documents related to:[/blue] {concept_text}")
        
        related_docs = processor.find_related_slops(concept_text, limit)
        
        if not related_docs:
            console.print(f"[yellow]No related documents found for '{concept_text}'[/yellow]")
            return
        
        table = Table(title=f"Documents related to '{concept_text}'")
        table.add_column("Document", style="cyan")
        table.add_column("Title", style="green")
        table.add_column("Confidence", justify="right")
        
        for doc in related_docs:
            table.add_row(
                doc.get('doc', 'N/A'),
                doc.get('title', 'Untitled'),
                doc.get('confidence', 'N/A')
            )
        
        console.print(table)
    
    @cli.command()
    @click.option('--port', '-p', default=8000, help='Port to serve on')
    @click.option('--host', '-h', default='0.0.0.0', help='Host to bind to')
    @click.option('--reload', is_flag=True, help='Enable auto-reload for development')
    def server(port, host, reload):
        """Start the slop.at FastAPI server"""
        import uvicorn
        from slopat.server.app import app

        console.print(f"[blue]Starting slop.at server...[/blue]")
        console.print(f"[green]🌐 Server will run at http://{host}:{port}[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        console.print("[bold]Available endpoints:[/bold]")
        console.print(f"  • GET  http://{host}:{port}/     - List all slops")
        console.print(f"  • POST http://{host}:{port}/slop  - Submit new slop")
        console.print(f"  • GET  http://{host}:{port}/{{hash}} - View slop by hash\n")

        try:
            uvicorn.run(
                "slopat.server.app:app",
                host=host,
                port=port,
                reload=reload,
                log_level="info"
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Server stopped[/yellow]")

    @cli.command()
    @click.option('--port', '-p', default=8000, help='Port to serve on')
    @click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
    @click.option('--output', '-o', type=click.Path(), help='Output directory to serve')
    def serve(port, host, output):
        """Start a web server to browse generated slop pages"""
        import http.server
        import socketserver
        import webbrowser
        import threading
        import time
        
        output_dir = Path(output) if output else Path.cwd() / "output"
        
        if not output_dir.exists():
            console.print(f"[red]Output directory does not exist: {output_dir}[/red]")
            console.print("[yellow]Try processing some files first with:[/yellow] slopat process data/")
            return
        
        # Check if there are any HTML files
        html_files = list(output_dir.glob("*.html"))
        if not html_files:
            console.print(f"[yellow]No HTML files found in {output_dir}[/yellow]")
            console.print("[yellow]Try processing some files first with:[/yellow] slopat process data/")
            return
        
        console.print(f"[blue]Starting web server...[/blue]")
        console.print(f"[dim]Serving:[/dim] {output_dir}")
        # Generate index page
        from slopat.web.index_generator import create_index_page
        index_path = create_index_page(output_dir)
        console.print(f"[dim]Generated index:[/dim] {index_path.name}")
        
        # Change to output directory
        import os
        original_cwd = os.getcwd()
        os.chdir(output_dir)
        
        try:
            # Create HTTP server
            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer((host, port), handler)
            
            # Auto-open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(f"http://{host}:{port}")
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            console.print(f"\n[green]🌐 Server running at http://{host}:{port}[/green]")
            console.print("[dim]Press Ctrl+C to stop[/dim]")
            
            # Show available files
            console.print("\n[bold]Available slops:[/bold]")
            for html_file in html_files:
                console.print(f"  • {html_file.name}")
            
            httpd.serve_forever()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping server...[/yellow]")
        except OSError as e:
            if "Address already in use" in str(e):
                console.print(f"[red]Port {port} is already in use. Try a different port with --port[/red]")
            else:
                console.print(f"[red]Server error: {e}[/red]")
        finally:
            os.chdir(original_cwd)
    
    return cli


def cli_main():
    """Entry point for the CLI script"""
    cli = main()
    cli()


if __name__ == "__main__":
    cli_main()
