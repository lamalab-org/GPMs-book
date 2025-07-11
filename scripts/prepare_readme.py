#!/usr/bin/env python3
"""
Script to generate README.md from LaTeX sections with extracted citations and bibliography.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

# Try to import bibtexparser for better BibTeX parsing
try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser

    BIBTEXPARSER_AVAILABLE = True
except ImportError:
    BIBTEXPARSER_AVAILABLE = False
    print(
        "Note: bibtexparser not available, using fallback parser. Install with: pip install bibtexparser"
    )


@dataclass
class Citation:
    """Represents a citation with its bibliographic information."""

    key: str
    title: str = ""
    year: str = ""
    url: str = ""
    authors: str = ""
    journal: str = ""


@dataclass
class Section:
    """Represents a document section with its hierarchy and citations."""

    level: int  # 1=section, 2=subsection, 3=subsubsection, etc.
    title: str
    label: str = ""
    citations: List[str] = None

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


class LaTeXParser:
    """Parser for LaTeX files to extract sections and citations."""

    def __init__(self):
        # Regex patterns for parsing
        self.section_pattern = re.compile(
            r"\\(sub)*section\*?\{([^}]+)\}(?:\s*\\label\{([^}]+)\})?", re.IGNORECASE
        )
        self.citation_pattern = re.compile(r"\\autocite\{([^}]+)\}")

    def parse_file(self, filepath: Path) -> List[Section]:
        """Parse a LaTeX file and extract sections with citations."""
        sections = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Error reading {filepath}: {e}")
            return sections

        # Find all sections
        section_matches = list(self.section_pattern.finditer(content))

        for i, match in enumerate(section_matches):
            # Determine section level
            section_type = match.group(0).lower()
            if "\\subsubsection" in section_type:
                level = 3
            elif "\\subsection" in section_type:
                level = 2
            elif "\\section" in section_type:
                level = 1
            else:
                level = 1

            title = match.group(2).strip()
            label = match.group(3) if match.group(3) else ""

            # Find citations in this section
            start_pos = match.end()
            end_pos = (
                section_matches[i + 1].start()
                if i + 1 < len(section_matches)
                else len(content)
            )
            section_content = content[start_pos:end_pos]

            # Find all citation groups and split multiple citations
            citation_groups = self.citation_pattern.findall(section_content)
            citations = []
            for group in citation_groups:
                # Split by comma and clean up each citation key
                keys = [key.strip() for key in group.split(",") if key.strip()]
                citations.extend(keys)

            # Remove duplicates while preserving order
            unique_citations = []
            seen = set()
            for cite in citations:
                if cite not in seen:
                    unique_citations.append(cite)
                    seen.add(cite)

            sections.append(
                Section(
                    level=level, title=title, label=label, citations=unique_citations
                )
            )

        return sections


class BibTeXParser:
    """Parser for BibTeX files with improved parsing."""

    def __init__(self):
        pass

    def parse_bib_file(self, filepath: Path) -> Dict[str, Citation]:
        """Parse a BibTeX file and return a dictionary of citations."""
        if BIBTEXPARSER_AVAILABLE:
            return self._parse_with_bibtexparser(filepath)
        else:
            return self._parse_with_regex(filepath)

    def _parse_with_bibtexparser(self, filepath: Path) -> Dict[str, Citation]:
        """Parse using the bibtexparser library."""
        citations = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                parser = BibTexParser(common_strings=True)
                bib_database = bibtexparser.load(f, parser=parser)

            for entry in bib_database.entries:
                key = entry.get("ID", "")

                # Get URL from various fields
                url = entry.get("url", entry.get("doi", entry.get("eprint", "")))
                if url and not url.startswith("http"):
                    if url.startswith("10."):  # DOI
                        url = f"https://doi.org/{url}"
                    elif "arxiv" in url.lower() or entry.get("eprint"):
                        arxiv_id = entry.get("eprint", url)
                        url = f"https://arxiv.org/abs/{arxiv_id}"

                citation = Citation(
                    key=key,
                    title=self._clean_latex(entry.get("title", "")),
                    year=self._clean_latex(str(entry.get("year", "")).strip()),
                    url=url,
                    authors=self._clean_latex(entry.get("author", "")),
                    journal=self._clean_latex(
                        entry.get("journal", entry.get("booktitle", ""))
                    ),
                )

                citations[key] = citation

        except Exception as e:
            print(f"Error parsing with bibtexparser: {e}")
            print("Falling back to regex parser...")
            return self._parse_with_regex(filepath)

        return citations

    def _parse_with_regex(self, filepath: Path) -> Dict[str, Citation]:
        """Parse using regex (fallback method)."""
        citations = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Error reading bibliography {filepath}: {e}")
            return citations

        # Split content by @ to get individual entries
        entries = re.split(r"\n@", content)

        for entry_text in entries:
            if not entry_text.strip():
                continue

            # Add @ back if it was split
            if not entry_text.startswith("@"):
                entry_text = "@" + entry_text

            # Extract entry type and key
            first_line_match = re.match(
                r"@(\w+)\s*\{\s*([^,\s]+)\s*,", entry_text, re.IGNORECASE
            )
            if not first_line_match:
                continue

            entry_type = first_line_match.group(1)
            key = first_line_match.group(2).strip()

            # Parse fields more carefully
            fields = {}

            # Pattern to match field = {value}, field = "value", or field = value,
            field_patterns = [
                r"(\w+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",  # field = {value}
                r'(\w+)\s*=\s*"([^"]*)"',  # field = "value"
                r"(\w+)\s*=\s*([^,\n}]+?)(?=\s*,|\s*\n|\s*})",  # field = value
            ]

            for pattern in field_patterns:
                matches = re.findall(pattern, entry_text)
                for field_name, field_value in matches:
                    field_name = field_name.lower()
                    if field_name not in fields:  # Don't overwrite
                        fields[field_name] = self._clean_latex(field_value.strip())

            # Get URL from various sources
            url = fields.get("url", fields.get("doi", fields.get("eprint", "")))
            if url and not url.startswith("http"):
                if url.startswith("10."):  # DOI
                    url = f"https://doi.org/{url}"
                elif "arxiv" in url.lower() or fields.get("eprint"):
                    arxiv_id = fields.get("eprint", url)
                    url = f"https://arxiv.org/abs/{arxiv_id}"

            citation = Citation(
                key=key,
                title=fields.get("title", ""),
                year=self._clean_latex(str(fields.get("year", "")).strip()),
                url=url,
                authors=fields.get("author", ""),
                journal=fields.get("journal", fields.get("booktitle", "")),
            )

            citations[key] = citation

        return citations

    def _clean_latex(self, text: str) -> str:
        """Clean LaTeX commands from text."""
        if not text:
            return text

        # Remove common LaTeX commands but preserve content
        text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\textit\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
        text = re.sub(r"\\[a-zA-Z]+", "", text)

        # Remove extra braces
        text = re.sub(r"\{([^}]*)\}", r"\1", text)

        # Clean up whitespace and trailing commas
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r",\s*$", "", text)  # Remove trailing comma
        return text.strip()


class ReadmeGenerator:
    """Generates README.md from parsed sections and citations."""

    def __init__(self, citations: Dict[str, Citation]):
        self.citations = citations

        # Define the desired section order
        self.section_order = [
            "introduction",
            "data_taxonomy",
            "architectures",
            "evals",
            "applications",
            "ai_scientists",
            "safety",
            "outlook_conclusions",
        ]

        # Map section files to display names
        self.section_display_names = {
            "introduction": "Introduction",
            "data_taxonomy": "The Shape and Structure of Chemical Data",
            "architectures": "Building Principles of GPMs",
            "evals": "Evaluations",
            "applications": "Applications",
            "ai_scientists": "Accelerating Applications",
            "safety": "Implications of GPMs: Education, Safety, and Ethics",
            "outlook_conclusions": "Outlook and Conclusions",
        }

    def _format_citation(self, citation: Citation) -> str:
        """Format a citation as 'Year - Title (hyperlinked)'."""
        title = citation.title if citation.title else f"Citation {citation.key}"
        year = citation.year if citation.year else "Unknown"

        if citation.url:
            return f"{year} - [{title}]({citation.url})"
        else:
            return f"{year} - {title}"

    # --- START MODIFICATION ---
    # New helper method to sort and write citations for a given list of keys.
    def _write_sorted_citations(self, f, cite_keys: List[str]):
        """
        Retrieves, sorts, and writes citations for a list of citation keys.
        The sorting is done by year in descending order.
        """
        if not cite_keys:
            return

        # Separate citations found in the bibliography from those that are missing.
        found_citations = []
        missing_keys = []
        for key in cite_keys:
            if key in self.citations:
                found_citations.append(self.citations[key])
            else:
                missing_keys.append(key)

        # Helper function to safely extract a numeric year for robust sorting.
        # It handles non-numeric values like 'in press' or '2024a'.
        def get_year_for_sort(citation: Citation) -> int:
            try:
                # Search for the first 4-digit number in the year string.
                year_match = re.search(r"\d{4}", str(citation.year))
                return int(year_match.group(0)) if year_match else 0
            except (ValueError, TypeError):
                # If year is invalid or not found, treat as 0 to sort it last.
                return 0

        # Sort the found citations by year in descending order.
        sorted_citations = sorted(found_citations, key=get_year_for_sort, reverse=True)

        # Write the sorted citations to the file.
        for citation in sorted_citations:
            ref_text = self._format_citation(citation)
            f.write(f"- {ref_text}\n")

        # List any missing citations at the end of the section.
        for key in missing_keys:
            f.write(f"- {key} *(citation not found in bibliography)*\n")

        f.write("\n")

    def generate(self, sections_by_file: Dict[str, List[Section]], output_path: Path):
        """Generate README.md file."""
        with open(output_path, "w", encoding="utf-8") as f:
            # (Preamble content remains unchanged)
            f.write("# General Purpose Models for the Chemical Sciences ✨\n\n")
            f.write("""![Status](https://img.shields.io/badge/status-active-brightgreen?style=flat-square)
    ![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-blue?style=flat-square)
    ![Platform](https://img.shields.io/badge/platform-web-blueviolet?style=flat-square)

    ## 📘 Read the Review

    You can read the review directly on
    or access it as a collaborative online book at:

    👉 [arXiv](https://arxiv.org/pdf/2507.07456)

    👉 [Online Book](https://lnkd.in/eWQVf4jJ)

    We also **welcome community contributions** — this is a living resource of references we ahve used in the review we aim to keep current with the evolving ecosystem. If you dont find your work or your favourite work here, please add it.

    ### ✨ Join the Community

    Help us grow and improve this resource by sharing your feedback or contributing directly via the online platform.

    Together, we can keep this reference **useful**, **relevant**, and **up to date** for everyone!
    This document provides an overview of the research sections and their associated references.
    """)
            f.write(
                "This document provides an overview of the research sections and their associated references.\n\n"
            )

            # Sort files according to the desired order
            sorted_files = []
            for section_key in self.section_order:
                if section_key in sections_by_file:
                    sorted_files.append(section_key)

            # Add any remaining files not in the predefined order
            for filename in sections_by_file:
                if filename not in sorted_files:
                    sorted_files.append(filename)

            for filename in sorted_files:
                sections = sections_by_file[filename]
                if not sections:
                    continue

                display_name = self.section_display_names.get(filename, filename)
                f.write(f"## {display_name}\n\n")

                for section in sections:
                    if section.title.lower() == display_name.lower():
                        # Section title is the same as the file name; just write sorted citations.
                        self._write_sorted_citations(f, section.citations)
                    else:
                        # Write the subsection header.
                        header_level = "#" * (section.level + 2)
                        f.write(f"{header_level} {section.title}\n\n")
                        # Write the sorted citations for this subsection.
                        self._write_sorted_citations(f, section.citations)

    # --- END MODIFICATION ---


def main():
    """Main function to orchestrate the README generation."""
    # Define paths
    base_path = Path("convert_book/extracted_latex")
    sections_path = base_path / "sections"
    bib_path = base_path / "references.bib"
    output_path = Path("README.md")

    # Check if paths exist
    if not sections_path.exists():
        print(f"Error: Sections directory not found at {sections_path}")
        sys.exit(1)

    if not bib_path.exists():
        print(f"Error: Bibliography file not found at {bib_path}")
        sys.exit(1)

    # Initialize parsers
    latex_parser = LaTeXParser()
    bib_parser = BibTeXParser()

    # Parse bibliography
    print("Parsing bibliography...")
    citations = bib_parser.parse_bib_file(bib_path)
    print(f"Found {len(citations)} citations in bibliography")

    # Debug: Print some citation info
    if citations:
        print("\nSample citations:")
        for i, (key, citation) in enumerate(list(citations.items())[:5]):
            print(
                f"  {key}: Year='{citation.year}' Title='{citation.title[:50]}...' URL='{citation.url}'"
            )
    else:
        print("No citations found - check BibTeX parsing")

    # Parse all LaTeX files
    print("\nParsing LaTeX sections...")
    sections_by_file = {}

    for tex_file in sections_path.glob("*.tex"):
        print(f"Processing {tex_file.name}...")
        sections = latex_parser.parse_file(tex_file)
        if sections:
            sections_by_file[tex_file.stem] = sections

    print(f"Processed {len(sections_by_file)} files")

    # Generate README
    print("Generating README...")
    generator = ReadmeGenerator(citations)
    generator.generate(sections_by_file, output_path)

    print(f"README.md generated successfully at {output_path}")

    # Print summary
    total_sections = sum(len(sections) for sections in sections_by_file.values())
    total_citations = sum(
        len(section.citations)
        for sections in sections_by_file.values()
        for section in sections
    )
    print(f"\nSummary:")
    print(f"- Total sections: {total_sections}")
    print(f"- Total citations found: {total_citations}")
    print(f"- Citations in bibliography: {len(citations)}")

    # Print missing citations
    all_cited_keys = set()
    for sections in sections_by_file.values():
        for section in sections:
            all_cited_keys.update(section.citations)

    missing_citations = all_cited_keys - set(citations.keys())
    if missing_citations:
        print(f"- Missing from bibliography: {len(missing_citations)}")
        print("  Missing keys:", list(missing_citations)[:10])  # Show first 10


if __name__ == "__main__":
    main()
