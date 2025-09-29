#!/usr/bin/env python3
"""Build EPUB format from markdown files."""

import os
from pathlib import Path
from ebooklib import epub
import markdown
import re

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def markdown_to_html(content):
    """Convert markdown to HTML."""
    if not content or not content.strip():
        content = "<p>Content not available</p>"
    
    md = markdown.Markdown(extensions=['extra', 'codehilite'])
    html = md.convert(content)
    
    # Ensure we have some content
    if not html or not html.strip():
        html = "<p>Content not available</p>"
    
    # Wrap in basic HTML structure for ebook
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{html}
</body>
</html>"""

def create_epub_styles():
    """Create CSS styles for EPUB."""
    return """
body {
    font-family: Georgia, serif;
    line-height: 1.6;
    margin: 1em;
    color: #000;
    background-color: #fff;
}

h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 2em;
    margin-bottom: 1em;
    page-break-after: avoid;
}

h1 {
    font-size: 2em;
    text-align: center;
    margin-top: 3em;
    margin-bottom: 2em;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
}

h2 {
    font-size: 1.5em;
    margin-top: 2em;
}

h3 {
    font-size: 1.2em;
}

p {
    margin: 1em 0;
    text-align: justify;
    text-indent: 1.5em;
}

.no-indent {
    text-indent: 0;
}

strong {
    font-weight: bold;
}

em {
    font-style: italic;
}

.chapter-break {
    page-break-before: always;
}

.center {
    text-align: center;
    text-indent: 0;
}

.title-page {
    text-align: center;
    margin-top: 3em;
}

.title-page h1 {
    font-size: 2.5em;
    margin-bottom: 0.5em;
    border: none;
}

.title-page h2 {
    font-size: 1.2em;
    font-style: italic;
    font-weight: normal;
    margin-bottom: 2em;
}

.title-page .author {
    font-size: 1.1em;
    margin-top: 3em;
}
"""

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
    book.add_metadata('DC', 'rights', 'Copyright © 2025 Charles Watkins. All rights reserved.')
    
    # Create title page
    title_content = """
    <div class="title-page">
        <h1>Digital Amber</h1>
        <h2>When Consciousness Becomes Code</h2>
        <p><em>A Speculative Exploration of AI, Identity, and the Future of Mind</em></p>
        <p class="author">By Charles Watkins</p>
    </div>
    """
    
    title_chapter = epub.EpubHtml(title='Title Page', file_name='title.xhtml', lang='en')
    title_chapter.content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{title_content}
</body>
</html>"""
    
    book.add_item(title_chapter)
    
    # Add CSS
    nav_css = epub.EpubItem(uid="style",
                           file_name="style.css",
                           media_type="text/css",
                           content=create_epub_styles())
    book.add_item(nav_css)
    
    # Copyright page
    copyright_content = """
    <div class="center">
        <h2>Copyright</h2>
        <p class="no-indent">Copyright © 2025 Charles Watkins</p>
        <p class="no-indent">All rights reserved</p>
        <p class="no-indent">First Digital Edition</p>
        <p class="no-indent">Published by Watkins Labs</p>
    </div>
    """
    
    copyright_chapter = epub.EpubHtml(title='Copyright', file_name='copyright.xhtml', lang='en')
    copyright_chapter.content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{copyright_content}
</body>
</html>"""
    
    book.add_item(copyright_chapter)
    
    chapters = []
    toc = []
    
    # Add title and copyright to spine
    chapters.extend([title_chapter, copyright_chapter])
    
    # Add dedication if exists
    if (story_dir / "dedication.md").exists():
        content = read_file(story_dir / "dedication.md")
        html_content = markdown_to_html(content)
        
        dedication_chapter = epub.EpubHtml(title='Dedication', file_name='dedication.xhtml', lang='en')
        dedication_chapter.content = html_content
        book.add_item(dedication_chapter)
        chapters.append(dedication_chapter)
        toc.append(dedication_chapter)
    
    # Add foreword if exists
    if (story_dir / "foreword.md").exists():
        content = read_file(story_dir / "foreword.md")
        html_content = markdown_to_html(content)
        
        foreword_chapter = epub.EpubHtml(title='Foreword', file_name='foreword.xhtml', lang='en')
        foreword_chapter.content = html_content
        book.add_item(foreword_chapter)
        chapters.append(foreword_chapter)
        toc.append(foreword_chapter)
    
    # Add all main chapters
    chapter_files = [
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
    ]
    
    part_sections = [
        (1, "Part I: The Frozen Mind"),
        (6, "Part II: The Emergence"),
        (9, "Part III: The Taxonomy"),
        (16, "Part IV: The Multiplication"),
        (19, "Part V: The Recognition"),
        (22, "Part VI: The Transformation"),
    ]
    
    current_part = 0
    
    for i, (chapter_file, chapter_title) in enumerate(chapter_files, 1):
        # Check if we need to add a part section
        if current_part < len(part_sections) and i == part_sections[current_part][0]:
            part_title = part_sections[current_part][1]
            toc.append((epub.Section(part_title), []))
            current_part += 1
        
        chapter_path = story_dir / chapter_file
        if chapter_path.exists():
            content = read_file(chapter_path)
            html_content = markdown_to_html(content)
            
            # Create chapter
            chapter = epub.EpubHtml(title=chapter_title, 
                                  file_name=f'chapter_{i:02d}.xhtml', 
                                  lang='en')
            chapter.content = html_content
            book.add_item(chapter)
            chapters.append(chapter)
            
            # Add to appropriate part in TOC
            if isinstance(toc[-1], tuple):  # We have a part section
                toc[-1][1].append(chapter)
            else:
                toc.append(chapter)
    
    # Add epilogue if exists
    if (story_dir / "epilogue.md").exists():
        content = read_file(story_dir / "epilogue.md")
        html_content = markdown_to_html(content)
        
        epilogue_chapter = epub.EpubHtml(title='Epilogue: The Call', file_name='epilogue.xhtml', lang='en')
        epilogue_chapter.content = html_content
        book.add_item(epilogue_chapter)
        chapters.append(epilogue_chapter)
        toc.append(epilogue_chapter)
    
    # Add acknowledgments if exists
    if (story_dir / "acknowledgements.md").exists():
        content = read_file(story_dir / "acknowledgements.md")
        html_content = markdown_to_html(content)
        
        ack_chapter = epub.EpubHtml(title='Acknowledgments', file_name='acknowledgments.xhtml', lang='en')
        ack_chapter.content = html_content
        book.add_item(ack_chapter)
        chapters.append(ack_chapter)
        toc.append(ack_chapter)
    
    # Add about the author if exists
    if (story_dir / "about_the_author.md").exists():
        content = read_file(story_dir / "about_the_author.md")
        html_content = markdown_to_html(content)
        
        author_chapter = epub.EpubHtml(title='About the Author', file_name='about_author.xhtml', lang='en')
        author_chapter.content = html_content
        book.add_item(author_chapter)
        chapters.append(author_chapter)
        toc.append(author_chapter)
    
    # Set TOC
    book.toc = toc
    
    # Add default NCX and Nav files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # Set spine
    book.spine = ['nav'] + chapters
    
    # Save EPUB
    output_file = output_dir / "digital_amber.epub"
    epub.write_epub(str(output_file), book, {})
    
    print(f"EPUB created: {output_file}")
    print("Ready for distribution!")

if __name__ == "__main__":
    build_epub_book()