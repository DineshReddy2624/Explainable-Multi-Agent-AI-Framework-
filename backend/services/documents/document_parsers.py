import os
import re
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ParsedPage:
    def __init__(self, page_number: int, text: str, tables: Optional[List[Dict[str, Any]]] = None, headings: Optional[List[str]] = None):
        self.page_number = page_number
        self.text = text
        self.tables = tables or []
        self.headings = headings or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "tables": self.tables,
            "headings": self.headings
        }


class ParsedDocument:
    def __init__(self, filename: str, file_type: str, pages: List[ParsedPage], metadata: Optional[Dict[str, Any]] = None):
        self.filename = filename
        self.file_type = file_type
        self.pages = pages
        self.metadata = metadata or {}

    @property
    def full_text(self) -> str:
        return "\n\n".join([p.text for p in self.pages if p.text.strip()])

    @property
    def total_pages(self) -> int:
        return len(self.pages)


class BaseDocumentParser:
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        raise NotImplementedError("Subclasses must implement parse()")


class PDFParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        pages = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                page_text = page.get_text("text") or ""
                
                # Extract simple heading candidates
                headings = [line.strip() for line in page_text.splitlines() if len(line.strip()) > 3 and len(line.strip()) < 60 and line.strip().isupper()]
                
                pages.append(ParsedPage(
                    page_number=page_num,
                    text=page_text.strip(),
                    headings=headings
                ))
            doc.close()
            logger.info(f"Successfully parsed PDF '{filename}' with {len(pages)} pages using PyMuPDF.")
        except Exception as e:
            logger.warning(f"PyMuPDF failed for '{filename}': {str(e)}. Falling back to plain text extraction.")
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")
            pages = [ParsedPage(page_number=1, text=content.strip())]

        return ParsedDocument(filename=filename, file_type="pdf", pages=pages)


class DOCXParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        pages = []
        try:
            import docx
            doc = docx.Document(file_path)
            full_text_lines = []
            headings = []
            tables_data = []

            for p in doc.paragraphs:
                txt = p.text.strip()
                if not txt:
                    continue
                if p.style and p.style.name.startswith("Heading"):
                    headings.append(txt)
                full_text_lines.append(txt)

            for table_idx, table in enumerate(doc.tables):
                t_rows = []
                for row in table.rows:
                    r_cells = [c.text.strip() for c in row.cells]
                    t_rows.append(r_cells)
                if t_rows:
                    tables_data.append({"table_id": table_idx + 1, "rows": t_rows})
                    full_text_lines.append(f"\n[Table {table_idx + 1}]\n" + "\n".join([" | ".join(r) for r in t_rows]))

            pages.append(ParsedPage(page_number=1, text="\n".join(full_text_lines), headings=headings, tables=tables_data))
            logger.info(f"Successfully parsed DOCX '{filename}'.")
        except Exception as e:
            logger.warning(f"python-docx failed for '{filename}': {str(e)}. Falling back to UTF-8 extraction.")
            with open(file_path, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")
            pages = [ParsedPage(page_number=1, text=content.strip())]

        return ParsedDocument(filename=filename, file_type="docx", pages=pages)


class TXTParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Split into pseudo-pages if huge text file
        lines = content.splitlines()
        pages = []
        chunk_lines = 100
        for idx in range(0, len(lines), chunk_lines):
            page_text = "\n".join(lines[idx:idx + chunk_lines]).strip()
            if page_text:
                pages.append(ParsedPage(page_number=(idx // chunk_lines) + 1, text=page_text))

        if not pages:
            pages = [ParsedPage(page_number=1, text=content.strip())]

        return ParsedDocument(filename=filename, file_type="txt", pages=pages)


class MarkdownParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        headings = re.findall(r'^#+\s+(.+)$', content, flags=re.MULTILINE)
        pages = [ParsedPage(page_number=1, text=content.strip(), headings=headings)]
        return ParsedDocument(filename=filename, file_type="md", pages=pages)


class HTMLParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_html = f.read()

        # Simple regex strip HTML tags while preserving text
        clean_text = re.sub(r'<script.*?>.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        pages = [ParsedPage(page_number=1, text=clean_text)]
        return ParsedDocument(filename=filename, file_type="html", pages=pages)


class JSONParser(BaseDocumentParser):
    def parse(self, file_path: str, filename: str) -> ParsedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_data = json.load(f)

        formatted_lines = []
        if isinstance(raw_data, list):
            for idx, item in enumerate(raw_data):
                formatted_lines.append(f"Record {idx + 1}: {json.dumps(item)}")
        elif isinstance(raw_data, dict):
            for k, v in raw_data.items():
                formatted_lines.append(f"Key '{k}': {json.dumps(v)}")
        else:
            formatted_lines.append(str(raw_data))

        pages = [ParsedPage(page_number=1, text="\n".join(formatted_lines))]
        return ParsedDocument(filename=filename, file_type="json", pages=pages)


class DocumentParserFactory:
    @staticmethod
    def get_parser(filename: str) -> BaseDocumentParser:
        lower_fn = filename.lower()
        if lower_fn.endswith(".pdf"):
            return PDFParser()
        elif lower_fn.endswith((".docx", ".doc")):
            return DOCXParser()
        elif lower_fn.endswith((".md", ".markdown")):
            return MarkdownParser()
        elif lower_fn.endswith((".html", ".htm")):
            return HTMLParser()
        elif lower_fn.endswith(".json"):
            return JSONParser()
        else:
            return TXTParser()


document_parser_factory = DocumentParserFactory()
