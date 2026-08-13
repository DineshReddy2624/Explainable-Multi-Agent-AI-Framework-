import re
from typing import List, Dict, Any, Optional
from services.documents.document_parsers import ParsedDocument, ParsedPage


class TextChunk:
    def __init__(
        self,
        chunk_id: str,
        document_id: int,
        org_id: str,
        chunk_index: int,
        page_number: int,
        section_title: Optional[str],
        text: str,
        metadata: Dict[str, Any]
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.org_id = org_id
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.section_title = section_title
        self.text = text
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "org_id": self.org_id,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "text": self.text,
            "metadata": self.metadata
        }


class ChunkingEngine:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, parsed_doc: ParsedDocument, document_id: int, org_id: str) -> List[TextChunk]:
        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        for page in parsed_doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            current_section = page.headings[0] if page.headings else None

            # Check if page contains embedded tables
            if page.tables:
                for tbl in page.tables:
                    tbl_rows = tbl.get("rows", [])
                    if tbl_rows:
                        header_row = tbl_rows[0]
                        tbl_str = f"Table (Page {page.page_number}): Headers: {', '.join(header_row)}\n" + "\n".join([" | ".join(r) for r in tbl_rows[1:]])
                        
                        global_chunk_idx += 1
                        chunk_id = f"doc_{document_id}_p{page.page_number}_c{global_chunk_idx}"
                        chunk_meta = {
                            "filename": parsed_doc.filename,
                            "file_type": parsed_doc.file_type,
                            "page_number": page.page_number,
                            "is_table": True,
                            "table_headers": header_row
                        }
                        chunks.append(TextChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            org_id=org_id,
                            chunk_index=global_chunk_idx,
                            page_number=page.page_number,
                            section_title=current_section,
                            text=tbl_str,
                            metadata=chunk_meta
                        ))

            # Recursive paragraph & sentence chunking for narrative text
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', page_text) if p.strip()]
            current_chunk_text = ""

            for para in paragraphs:
                if len(current_chunk_text) + len(para) <= self.chunk_size:
                    current_chunk_text += ("\n\n" + para) if current_chunk_text else para
                else:
                    if current_chunk_text:
                        global_chunk_idx += 1
                        chunk_id = f"doc_{document_id}_p{page.page_number}_c{global_chunk_idx}"
                        chunk_meta = {
                            "filename": parsed_doc.filename,
                            "file_type": parsed_doc.file_type,
                            "page_number": page.page_number,
                            "is_table": False
                        }
                        chunks.append(TextChunk(
                            chunk_id=chunk_id,
                            document_id=document_id,
                            org_id=org_id,
                            chunk_index=global_chunk_idx,
                            page_number=page.page_number,
                            section_title=current_section,
                            text=current_chunk_text,
                            metadata=chunk_meta
                        ))
                        # Keep overlap
                        overlap_start = max(0, len(current_chunk_text) - self.chunk_overlap)
                        current_chunk_text = current_chunk_text[overlap_start:] + "\n\n" + para
                    else:
                        # Para itself exceeds chunk_size, split by sentences
                        sentences = re.split(r'(?<=[.!?])\s+', para)
                        for sent in sentences:
                            if len(current_chunk_text) + len(sent) <= self.chunk_size:
                                current_chunk_text += (" " + sent) if current_chunk_text else sent
                            else:
                                if current_chunk_text:
                                    global_chunk_idx += 1
                                    chunk_id = f"doc_{document_id}_p{page.page_number}_c{global_chunk_idx}"
                                    chunks.append(TextChunk(
                                        chunk_id=chunk_id,
                                        document_id=document_id,
                                        org_id=org_id,
                                        chunk_index=global_chunk_idx,
                                        page_number=page.page_number,
                                        section_title=current_section,
                                        text=current_chunk_text,
                                        metadata={"filename": parsed_doc.filename, "file_type": parsed_doc.file_type, "page_number": page.page_number}
                                    ))
                                current_chunk_text = sent

            if current_chunk_text:
                global_chunk_idx += 1
                chunk_id = f"doc_{document_id}_p{page.page_number}_c{global_chunk_idx}"
                chunks.append(TextChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    org_id=org_id,
                    chunk_index=global_chunk_idx,
                    page_number=page.page_number,
                    section_title=current_section,
                    text=current_chunk_text,
                    metadata={"filename": parsed_doc.filename, "file_type": parsed_doc.file_type, "page_number": page.page_number}
                ))

        return chunks


chunking_engine = ChunkingEngine()
