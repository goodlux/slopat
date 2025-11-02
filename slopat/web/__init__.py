"""Web interface and HTML generation"""

from .html_generator import HTMLGenerator, SlopPage, save_slop_page
from .index_generator import generate_index_page, create_index_page

__all__ = [
    "HTMLGenerator",
    "SlopPage",
    "save_slop_page",
    "generate_index_page",
    "create_index_page"
]
