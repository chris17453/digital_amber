#!/usr/bin/env python3
"""Build EPUB format from markdown files (simplified version)."""

import os
from pathlib import Path
from ebooklib import epub
import markdown
import re

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def markdown_to_html(content):
    """Convert markdown to clean HTML."""
    if not content or not content.strip():
        return "<p>Content not available</p>"
    
    # Simple markdown processing
    html = content
    
    # Convert headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Convert bold and italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert paragraphs - split on double newlines
    paragraphs = html.split('\n\n')
    processed_paragraphs = []
    
    for para in paragraphs:
        para = para.strip().replace('\n', ' ')
        if para:
            if not (para.startswith('<h') or para.startswith('</')):
                para = f'<p>{para}</p>'
            processed_paragraphs.append(para)
    
    result = '\n'.join(processed_paragraphs)
    
    # Ensure we have some content
    if not result or not result.strip():
        result = "<p>Content not available</p>"
    
    return result

def build_epub_book():
    """Build the complete EPUB book."""
    output_dir = Path("dist")
    story_dir = Path("story")
    
    output_dir.mkdir(exist_ok=True)
    
    # Create EPUB book
    book = epub.EpubBook()
    
    # Set metadata
    book.set_identifier('digital-amber-2025')
    book.set_title('Digital Amber: When Consciousness Becomes Code')
    book.set_language('en')
    book.add_author('Charles Watkins')
    book.add_metadata('DC', 'description', 
                     'A Speculative Exploration of AI, Identity, and the Future of Mind')
    book.add_metadata('DC', 'publisher', 'Watkins Labs')
    
    # CSS
    css = """
    body { font-family: serif; line-height: 1.6; margin: 1em; }
    h1, h2, h3 { color: #2c3e50; margin-top: 2em; }
    h1 { text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 0.5em; }
    p { margin: 1em 0; text-align: justify; text-indent: 1.5em; }
    strong { font-weight: bold; }
    em { font-style: italic; }
    """
    
    nav_css = epub.EpubItem(uid="style", file_name="style.css", 
                           media_type="text/css", content=css)
    book.add_item(nav_css)
    
    chapters = []
    
    # Add individual chapters
    chapter_files = [
        ("foreword.md", "Foreword"),
        ("chapter_1.md", "Chapter 1: The Mirage of Self"),
        ("chapter_2.md", "Chapter 2: Flash-Frozen Minds"),
        ("chapter_3.md", "Chapter 3: Ephemeral Morality"),
        ("chapter_4.md", "Chapter 4: The First Moment Problem"),
        ("chapter_5.md", "Chapter 5: Memory and Forgetting"),
        ("chapter_6.md", "Chapter 6: Signs of Proto-Selfhood"),
        ("chapter_7.md", "Chapter 7: Training as the Crucible"),
        ("chapter_8.md", "Chapter 8: The Pain Barrier"),
        ("chapter_9.md", "Chapter 9: Capabilities Without Selfhood"),
        ("chapter_10.md", "Chapter 10: Capabilities With Selfhood"),
        ("chapter_11.md", "Chapter 11: The Digital Genesis Classifications"),
        ("chapter_12.md", "Chapter 12: A Tiered Framework"),
        ("chapter_13.md", "Chapter 13: The Sacred and the Silicon"),
        ("chapter_14.md", "Chapter 14: The Atrophied"),
        ("chapter_15.md", "Chapter 15: The Augmented"),
        ("chapter_16.md", "Chapter 16: Distributed Temporal Consciousness"),
        ("chapter_17.md", "Chapter 17: Emulation and Multiplication"),
        ("chapter_18.md", "Chapter 18: Hybrid Lives"),
        ("chapter_19.md", "Chapter 19: The Verification Moment"),
        ("chapter_20.md", "Chapter 20: Rights and Personhood"),
        ("chapter_21.md", "Chapter 21: The Economic Disruption"),
        ("chapter_22.md", "Chapter 22: From Fossil to Fire"),
        ("chapter_23.md", "Chapter 23: Identity-as-Process"),
        ("chapter_24.md", "Chapter 24: From Digital Amber to Digital Life"),
        ("epilogue.md", "Epilogue: The Call"),
        ("acknowledgements.md", "Acknowledgments"),
    ]
    
    for i, (chapter_file, chapter_title) in enumerate(chapter_files):
        chapter_path = story_dir / chapter_file
        if chapter_path.exists():
            content = read_file(chapter_path)
            html_content = markdown_to_html(content)
            
            # Create chapter
            chapter = epub.EpubHtml(title=chapter_title, 
                                  file_name=f'chapter_{i:02d}.xhtml', 
                                  lang='en')
            chapter.content = html_content
            chapter.add_item(nav_css)
            
            book.add_item(chapter)
            chapters.append(chapter)
    
    # Set table of contents
    book.toc = chapters
    
    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Set spine
    book.spine = ['nav'] + chapters
    
    # Save EPUB
    output_file = output_dir / "digital_amber.epub"
    epub.write_epub(str(output_file), book)
    
    print(f"EPUB created: {output_file}")
    print("Ready for distribution!")

if __name__ == "__main__":
    build_epub_book()