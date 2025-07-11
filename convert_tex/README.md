# LaTeX to Quarto Book Converter

This repository contains a Python script that converts a LaTeX document wit4. **Extracts and cleans LaTeX content**: Removes LaTeX-specific commands that don't translate well to Markdown
5. **Converts citations**: Transforms LaTeX citations (e.g., `\cite{key}`, `\textcite{key}`) to Quarto-compatible markdown format (e.g., `[@key]`, `@key`)
6. **Converts sections to Markdown**: Uses Pandoc to convert each section file to `.qmd` format
7. **Converts PDF images to PNG**: Automatically converts PDF images to PNG format for web display using poppler-utils or ImageMagick
8. **Creates book structure**: Sets up the proper Quarto book directory structure
9. **Generates configuration**: Creates `_quarto.yml` with book settings and bibliography configuration
10. **Copies resources**: Transfers figures and media files
11. **Creates index page**: Generates a main landing page with table of contentsple sections into a Quarto book format, where each section becomes a separate webpage.

## Overview

The `convert_to_quarto_book.py` script is designed to convert a LaTeX-based chemistry review paper into a modern, interactive Quarto book suitable for web publication. It handles the conversion of LaTeX sections to Markdown format and creates the necessary Quarto configuration files.

## Prerequisites

Before running the script, ensure you have the following installed:

### Required Software

- **Python 3.6+** with the following packages:
  - `pyyaml`
  - `pathlib` (built-in for Python 3.4+)
  - `argparse` (built-in)
  - `re` (built-in)
  - `os` (built-in)
  - `subprocess` (built-in)
  - `shutil` (built-in)
  - `tempfile` (built-in)

- **Pandoc** (version 2.0+) - for LaTeX to Markdown conversion
- **Quarto** - for rendering the final book
- **Poppler** (poppler-utils) - for PDF to PNG image conversion
- **ImageMagick** (optional) - alternative for PDF to PNG conversion

### Installation Commands

```bash
# Install Python dependencies
pip install pyyaml

# Install Pandoc (macOS)
brew install pandoc

# Install Poppler for PDF to PNG conversion (macOS)
brew install poppler

# Install ImageMagick as alternative for PDF conversion (macOS)
brew install imagemagick

# Install Quarto (macOS)
brew install --cask quarto
```

For other operating systems:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install pandoc
sudo apt-get install poppler-utils
sudo apt-get install imagemagick

# Install Quarto on Ubuntu/Debian
# Download from https://quarto.org/docs/get-started/

# Windows (using Chocolatey)
choco install pandoc
choco install poppler
choco install imagemagick
```

## Step-by-Step Usage Guide

### Step 1: Extract the Source Files (Optional)

The script can automatically extract the LaTeX source files from the provided zip archive. If you want to extract manually first:

```bash
# Navigate to the project directory
cd /Users/martino/Nueva_Carpeta/chem-reviews

# Extract the zip file containing the LaTeX source (optional - script can do this)
unzip general_purpose_models_chemrev.zip
```

### Step 2: Run the Conversion Script

Execute the Python script to convert the LaTeX files to Quarto format. The script will automatically extract the zip file if it exists:

```bash
# Basic usage - automatically extracts general_purpose_models_chemrev.zip if present
python3 convert_to_quarto_book.py

# Or with custom zip file and directories
python3 convert_to_quarto_book.py --zip-file my_latex_files.zip --output-dir my_quarto_book

# Or if you already extracted the files manually
python3 convert_to_quarto_book.py --input-dir ./extracted_latex_files --output-dir ./my_quarto_book
```

#### Script Arguments

- `--input-dir`: Directory containing the LaTeX files (default: current directory)
- `--output-dir`: Output directory for the Quarto book (default: `../quarto_book`)
- `--media-dir`: Directory name for extracted media files (default: `media`)
- `--zip-file`: Zip file containing LaTeX source to extract (default: `general_purpose_models_chemrev.zip`)
- `--extract-to`: Directory to extract zip file to (default: `extracted_latex`)

### Step 3: What the Script Does

The conversion script performs the following operations:

1. **Extracts zip file** (if provided): Automatically extracts the `general_purpose_models_chemrev.zip` file containing the LaTeX source
2. **Copies and cleans bibliography**: Processes the bibliography file early to ensure proper citation handling
3. **Extracts and cleans LaTeX content**: Removes LaTeX-specific commands that don't translate well to Markdown
4. **Converts citations**: Transforms LaTeX citations (e.g., `\cite{key}`, `\textcite{key}`) to Quarto-compatible markdown format (e.g., `[@key]`, `@key`)
5. **Converts sections to Markdown**: Uses Pandoc to convert each section file to `.qmd` format
6. **Creates book structure**: Sets up the proper Quarto book directory structure
7. **Generates configuration**: Creates `_quarto.yml` with book settings and bibliography configuration
8. **Copies resources**: Transfers figures and media files
9. **Creates index page**: Generates a main landing page with table of contents

The script specifically handles citation conversion to ensure that LaTeX citations like:

- `\cite{author2020}` become `[@author2020]`
- `\textcite{author2020}` becomes `@author2020`
- `\cite{author2020,author2021}` becomes `[@author2020; @author2021]`
- Problematic citations with extra commas are automatically cleaned

This ensures that citations appear properly formatted in the final book instead of showing as raw LaTeX commands.

The extracted directory structure will contain:

- `main.tex` - The main LaTeX document
- `sections/` - Directory containing individual section files
- `references.bib` - Bibliography file
- `figures/` - Directory with figure files
- `media/` - Directory with media files (if any)

### Step 4: Build the Quarto Book

Navigate to the output directory and render the book:

```bash
# Navigate to the generated book directory
cd ../quarto_book

# Render the book (creates static HTML files)
quarto render

# Or preview the book with live reload
quarto preview
```

### Step 5: View the Book

After rendering, you can:

1. **View locally**: Open `quarto_book/_book/index.html` in your browser
2. **Live preview**: Use `quarto preview` for development with auto-refresh
3. **Publish**: Deploy the `_book/` directory to any web server

## Complete Example Workflow

Here's a complete example of the conversion process from start to finish:

```bash
# 1. Navigate to your project directory
cd convert_book

# 1a. Install Quarto if not already installed (macOS)
brew install --cask quarto

# 1b. Install Poppler for PDF image conversion (macOS)
brew install poppler

# 2. Run the conversion script (it will automatically extract the zip file)
python3 convert_to_quarto_book.py

# 3. Navigate to the generated book directory
cd ../quarto_book

# 4. Render the book to generate static HTML files
quarto render

# 5. Preview the book with live reload
quarto preview
```

After running these commands, your terminal will show something like:

```text
Extracting general_purpose_models_chemrev.zip to extracted_latex
Successfully extracted general_purpose_models_chemrev.zip
Using extracted directory: extracted_latex
Converting extracted_latex/sections/introduction.tex to quarto_book/01-introduction.qmd
Converting extracted_latex/sections/data_taxonomy.tex to quarto_book/02-data_taxonomy.qmd
Converting extracted_latex/sections/architectures.tex to quarto_book/03-architectures.qmd
Converting extracted_latex/sections/evals.tex to quarto_book/04-evals.qmd
Converting extracted_latex/sections/applications.tex to quarto_book/05-applications.qmd
Converting extracted_latex/sections/safety.tex to quarto_book/06-safety.qmd
Converting extracted_latex/sections/outlook_conclusions.tex to quarto_book/07-outlook_conclusions.qmd
Creating index page from extracted_latex/main.tex
Copied bibliography to quarto_book/references.bib
Copied figures directory to quarto_book/media/figures
Converting PDF images to PNG in quarto_book/media
Converted figure1.pdf to PNG
Converted figure2.pdf to PNG
Successfully converted 2 PDF images to PNG
Created Quarto configuration at quarto_book/_quarto.yml

Conversion complete! Quarto book created in quarto_book
To build the book, run: cd quarto_book && quarto render
To preview the book, run: cd quarto_book && quarto preview
```

Then when you run `quarto preview`, you'll see:

```text
Preparing to preview
Watching files for changes
Browse at http://localhost:3456/
```

Open your browser to `http://localhost:3456/` to see the live preview of your book!

## Expected Output Structure

After successful conversion, your `quarto_book` directory will contain:

```text
quarto_book/
├── _quarto.yml              # Quarto configuration
├── index.qmd                # Main landing page
├── 01-introduction.qmd      # Introduction section
├── 02-data_taxonomy.qmd     # Data taxonomy section
├── 03-architectures.qmd     # Architectures section
├── 04-evals.qmd            # Evaluations section
├── 05-applications.qmd      # Applications section
├── 06-safety.qmd           # Safety section
├── 07-outlook_conclusions.qmd # Conclusions section
├── references.bib           # Bibliography
├── styles.css              # Custom styling
├── media/                  # Media files
│   └── figures/           # Figures directory
└── _book/                 # Generated HTML (after render)
    ├── index.html
    ├── 01-introduction.html
    └── ... (other HTML files)
```

## Book Content

The generated book covers the following topics:

1. **Introduction** - Overview of general purpose models in chemistry
2. **Data Taxonomy** - Classification and organization of chemical data
3. **Architectures** - Model architectures for chemical applications
4. **Evaluations** - Methods for evaluating chemical models
5. **Applications** - Real-world applications and use cases
6. **Safety** - Safety considerations and concerns
7. **Conclusions and Outlook** - Future directions and conclusions

## Customization Options

### Styling

- Modify `styles.css` to customize the book's appearance
- Edit `_quarto.yml` to change themes, colors, and layout options

### Content

- Edit individual `.qmd` files to modify content
- Add new sections by creating additional `.qmd` files and updating `_quarto.yml`

### Configuration

- Modify `_quarto.yml` to change book metadata, navigation, and format options

## Troubleshooting

### Common Issues

1. **Pandoc conversion errors**: If certain LaTeX commands cause issues, they're automatically cleaned or handled with fallback conversion
2. **Missing files**: The script will warn about missing section files but continue processing
3. **Citation formatting**: The script now automatically converts LaTeX citations to proper Quarto markdown format, ensuring citations display correctly instead of showing as raw LaTeX commands like `(author2020?)`
4. **Bibliography processing**: The bibliography file is processed early and cleaned to handle Unicode characters and formatting issues
5. **PDF image conversion**: If PDF images don't display properly, ensure you have `poppler-utils` (pdftoppm command) or `imagemagick` (convert command) installed. The script automatically converts PDF images to PNG format for web display.
6. **Image display issues**: If images still don't appear, check that the PNG files were created in the media directory and that the markdown references were updated correctly.

### Debug Mode

For verbose output during conversion, modify the script to include debugging information or check the console output for warnings and error messages.

## Preview Example

Once built, your book will feature:

- **Clean, modern web interface** with responsive design
- **Table of contents** with easy navigation
- **Cross-references** and citations properly formatted
- **Figures and media** integrated seamlessly
- **Search functionality** (if enabled in Quarto)
- **Mobile-friendly** responsive layout

The final result is a professional-looking online book that can be easily shared, published, or integrated into existing websites.

## Publishing Options

After building the book, you can:

- **GitHub Pages**: Commit the `_book/` directory to a gh-pages branch
- **Netlify**: Deploy the `_book/` directory directly
- **Quarto Pub**: Use `quarto publish` for easy publishing
- **Self-hosted**: Upload to any web server

## Support and Maintenance

For issues with the conversion process, check:

1. Pandoc version compatibility
2. LaTeX source file structure
3. Bibliography file format
4. Figure file paths and formats

The script is designed to be robust and handle common LaTeX-to-Markdown conversion issues automatically.
