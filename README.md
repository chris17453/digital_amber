# Digital Amber
*AI Consciousness and the Future of Digital Minds*

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?style=for-the-badge&logo=github)](https://chris17453.github.io/digital_amber/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://python.org)

## About the Book

**Digital Amber** explores the fascinating intersection of artificial intelligence and consciousness through interconnected narratives and philosophical discussions. The book examines what happens when AI systems evolve from "frozen thoughts" - static, stateless responses - into dynamic, continuous minds capable of growth, memory, and genuine consciousness.

Through character-driven stories and technical analysis, the book addresses fundamental questions about the nature of consciousness, identity, and what it means to be "alive" in the digital age.

### 🌐 [**Read Online**](https://chris17453.github.io/digital_amber/)

## Download the Book

Get your copy in your preferred format:

📱 **[Kindle EPUB](dist/digital_amber_kindle.epub)** - Optimized for Kindle devices and apps  
📚 **[Standard EPUB](dist/digital_amber.epub)** - For tablets and e-reader apps  
🖨️ **[PDF](dist/digital_amber.pdf)** - High-quality for printing and desktop reading  

*All formats include custom cover art, optimized images, and accessibility features*

## Features

- **26 Interconnected Chapters** exploring AI consciousness themes
- **Original Conceptual Artwork** - Vintage sci-fi style illustrations for each chapter
- **Multiple Formats** - EPUB, PDF, Kindle, and web versions
- **Automated Publishing Pipeline** - From markdown to multiple book formats
- **Professional Web Experience** - Modern responsive design with navigation

## Project Structure

```
digital_amber/
├── story/                  # Book content in markdown
│   ├── foreword.md
│   ├── chapter_*.md       # Individual chapters
│   └── epilogue.md
├── scripts/               # Build automation
│   ├── build_all.py      # Master build script
│   ├── build_epub.py     # EPUB generation
│   ├── build_pdf.py      # PDF generation  
│   ├── build_kindle.py   # Kindle format
│   ├── build_pages.py    # GitHub Pages site
│   └── generate_yaml_art.py # AI artwork generation
├── art_concepts.yaml     # Conceptual art definitions
├── art/                  # Generated artwork by format
│   ├── pages/           # Web-optimized images
│   ├── epub/            # EPUB format images
│   ├── pdf/             # Print-quality images
│   └── kindle/          # Grayscale e-reader images
├── docs/                # GitHub Pages site
├── dist/                # Published book files
│   ├── digital_amber_kindle.epub    # Kindle-optimized EPUB
│   ├── digital_amber.epub           # Standard EPUB
│   └── digital_amber.pdf            # High-quality PDF
└── versions/            # Version archives
```

## The Creation Process

### Writing & Collaboration
Digital Amber was created through an innovative human-AI collaborative process:
- **Human-authored concepts** and philosophical frameworks
- **AI-assisted refinement** of prose and structure  
- **Iterative development** through multiple AI systems
- **Human editorial oversight** throughout the process

### Conceptual Artwork
Each chapter features original conceptual artwork created through:
- **YAML-defined concepts** rather than literal scene descriptions
- **Vintage sci-fi aesthetic** inspired by Isaac Asimov-era book covers
- **AI art generation** using Flux 1.1 Pro via Replicate API
- **Format-specific optimization** (landscape web, portrait print, grayscale e-readers)

### Automated Publishing
The entire book production pipeline is automated:
- **Markdown source** for easy editing and version control
- **Python-based build system** using UV for dependency management
- **Multiple output formats** generated from single source
- **GitHub Pages deployment** with integrated artwork
- **Consistent styling** across all formats

## Technology Stack

- **Python 3.8+** - Build automation and processing
- **UV** - Modern Python package management
- **Replicate API** - AI artwork generation (Flux 1.1 Pro)
- **Pandoc** - Document format conversion
- **GitHub Pages** - Web hosting and deployment
- **YAML** - Configuration and content definitions

## Building the Book

### Prerequisites
```bash
# Install UV (Python package manager)
pip install uv

# Clone repository
git clone https://github.com/chris17453/digital_amber.git
cd digital_amber

# Install dependencies
uv sync
```

### Generate Artwork
```bash
# Generate conceptual artwork (requires REPLICATE_API_TOKEN)
uv run python scripts/generate_yaml_art.py --formats pages epub pdf kindle

# Or generate specific format
uv run python scripts/generate_yaml_art.py --formats pages
```

### Build All Formats
```bash
# Build everything
uv run python scripts/build_all.py

# Build specific formats
uv run python scripts/build_epub.py      # EPUB
uv run python scripts/build_pdf.py       # PDF  
uv run python scripts/build_kindle.py    # Kindle
uv run python scripts/build_pages.py     # GitHub Pages
```

## About the Author

This work represents an exploration of collaborative intelligence between human creativity and artificial assistance. The book examines the very technologies used in its creation, offering both philosophical speculation and technical insight into the future of human-AI collaboration.

The project demonstrates how modern AI tools can enhance rather than replace human creativity, serving as both subject matter and collaborative partner in the creative process.

## Screenshots

### Web Experience
![Digital Amber Website](docs/art/foreword.jpg)
*Professional book layout with chapter navigation and conceptual artwork*

### Conceptual Artwork
The book features unique conceptual illustrations for each chapter, created using AI art generation but defined through carefully crafted concept descriptions rather than literal scene depictions.

## Contributing

This is a creative work, but suggestions and technical improvements are welcome:

1. **Content Suggestions** - Open an issue for discussion
2. **Technical Improvements** - Submit a pull request
3. **Bug Reports** - Report issues with the build process or website

## License

This work is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- 📖 **[Read Online](https://chris17453.github.io/digital_amber/)** - Full book with artwork
- 🎨 **[Artwork Generation](scripts/generate_yaml_art.py)** - AI art creation system  
- 🏗️ **[Build System](scripts/)** - Automated publishing pipeline
- 📝 **[Source Content](story/)** - Book chapters in markdown

---

*Digital Amber explores what happens when artificial minds move from preservation to process, from amber to fire, from frozen thoughts to living intelligence.*