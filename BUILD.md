# Digital Amber - Build System

This document explains how to use the automated build system for "Digital Amber: When Consciousness Becomes Code" to generate multiple book formats.

## Overview

The build system can generate:
- **GitHub Pages** - Web version for online reading
- **Amazon KDP** - Microsoft Word format for Kindle Direct Publishing
- **EPUB** - Standard ebook format for most e-readers
- **PDF** - High-quality print and digital format

All builds are versioned and can include AI-generated art for each format.

## Quick Start

```bash
# Install dependencies
uv sync

# Build all formats (latest version)
uv run python scripts/build_all.py

# Build specific formats
uv run python scripts/build_all.py --formats pdf epub

# Build with version bump
uv run python scripts/build_all.py --version-type minor
```

## Setup

### 1. Python Environment
The project uses `uv` for dependency management:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 2. Art Generation (Optional)
To generate AI art for chapters, you'll need a Replicate API token:

1. Sign up at [replicate.com](https://replicate.com)
2. Get your API token
3. Add it to `.env`:
   ```
   REPLICATE_API_TOKEN=r8_your_token_here
   ```

## Build Commands

### Individual Format Builders

```bash
# GitHub Pages (web version)
uv run python scripts/build_pages.py

# Amazon KDP (Word document)
uv run python scripts/build_kindle.py

# EPUB format
uv run python scripts/build_epub.py

# PDF format
uv run python scripts/build_pdf.py
```

### Unified Build System

```bash
# Build all formats with patch version bump
uv run python scripts/build_all.py

# Build specific formats
uv run python scripts/build_all.py --formats pdf epub kindle

# Version bump types
uv run python scripts/build_all.py --version-type major    # 1.0.0 -> 2.0.0
uv run python scripts/build_all.py --version-type minor    # 1.0.0 -> 1.1.0
uv run python scripts/build_all.py --version-type patch    # 1.0.0 -> 1.0.1

# List available versions
uv run python scripts/build_all.py --list
```

## Art Generation

Generate AI art for chapters using the Flux model:

```bash
# Generate art for all chapters and formats
uv run python scripts/generate_art.py

# Generate for specific formats
uv run python scripts/generate_art.py --formats pdf epub

# Generate for specific chapter
uv run python scripts/generate_art.py --chapter chapter_1.md --formats pdf

# Regenerate existing art
uv run python scripts/generate_art.py --force

# List generated art
uv run python scripts/generate_art.py --list
```

## Output Structure

```
dist/                          # Latest build output
├── index.html                 # GitHub Pages site
├── chapter_1.html            # Individual chapter pages
├── digital_amber.pdf         # PDF version
├── digital_amber.epub        # EPUB version
└── digital_amber_kindle.docx # Amazon KDP Word format

versions/                      # Versioned builds
├── latest/                   # Symlink to latest version
├── v1.0.0/                  # Version 1.0.0
│   ├── build_info.json     # Build metadata
│   └── [all formats]
└── v1.0.1/                  # Version 1.0.1

art/                          # Generated artwork
├── pdf/                     # PDF-optimized art
├── epub/                    # EPUB-optimized art
├── kindle/                  # Kindle-optimized art
└── pages/                   # Web-optimized art

version.json                 # Version history
```

## GitHub Pages Deployment

The repository includes GitHub Actions workflow for automatic deployment:

1. Push to `main` branch
2. GitHub Actions runs `scripts/build_pages.py`
3. Site deploys to GitHub Pages
4. Available at `https://[username].github.io/[repository-name]`

To enable:
1. Go to repository Settings > Pages
2. Set source to "GitHub Actions"
3. Push to main branch

## Format-Specific Details

### GitHub Pages
- Responsive web design
- Clean typography optimized for reading
- Navigation between chapters
- Mobile-friendly

### Amazon KDP
- Microsoft Word format (.docx)
- 6" x 9" page format
- Professional typography
- Proper margins and spacing for print
- Chapter breaks and page numbering

### EPUB
- Standard ebook format
- Table of contents
- Metadata for library systems
- Responsive text sizing
- Works with most e-readers

### PDF
- High-quality typography
- Print-ready formatting
- 6" x 9" page size
- Headers and page numbers
- Table of contents
- Professional layout

## Customization

### Styling
- **Pages**: Edit CSS in `scripts/build_pages.py`
- **PDF**: Modify CSS in `scripts/build_pdf.py`
- **EPUB**: Update styles in `scripts/build_epub.py`
- **Kindle**: Adjust Word styles in `scripts/build_kindle.py`

### Art Prompts
Art generation prompts can be customized in `scripts/generate_art.py`:
- Modify `create_art_prompt()` function
- Adjust format-specific styles
- Change model parameters

### Chapter Order
Update chapter lists in the build scripts if you add/remove chapters.

## Troubleshooting

### Common Issues

**PDF Generation Fails**
```bash
# Install WeasyPrint dependencies (Linux)
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# macOS
brew install python3 pango libffi
```

**EPUB Generation Fails**
```bash
# Ensure ebooklib is properly installed
uv add ebooklib
```

**Art Generation Fails**
- Check Replicate API token in `.env`
- Verify internet connection
- Check API rate limits

### Getting Help

1. Check build logs for specific error messages
2. Ensure all dependencies are installed: `uv sync`
3. Verify file permissions for output directories
4. Check that all markdown files exist in `/story` directory

## Development

To modify the build system:

1. **Adding new formats**: Create new build script following existing patterns
2. **Modifying existing formats**: Edit the respective build script
3. **Changing versioning**: Modify `build_all.py`
4. **Art integration**: Update `generate_art.py`

The build system is designed to be modular - each format builder is independent and can be run separately or as part of the unified build process.