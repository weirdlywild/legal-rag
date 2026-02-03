"""PDF processing service using pymupdf4llm."""

import re
import uuid
from io import BytesIO
from typing import BinaryIO

import tiktoken
import pymupdf4llm
import pymupdf

from ..config import get_settings, Settings
from ..models.documents import Chunk, ProcessedDocument


class PDFProcessor:
    """Service for processing PDF documents into chunks."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the PDF processor."""
        self.settings = settings or get_settings()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.tokenizer.encode(text))

    def _split_into_chunks(
        self,
        text: str,
        max_tokens: int,
        overlap_tokens: int,
    ) -> list[str]:
        """
        Split text into chunks with overlap.

        Uses sentence boundaries when possible.
        """
        if not text.strip():
            return []

        # Split into sentences (rough approximation)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence is too long, split by characters
            if sentence_tokens > max_tokens:
                # Flush current chunk
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence into smaller pieces
                words = sentence.split()
                temp_chunk = []
                temp_tokens = 0
                for word in words:
                    word_tokens = self.count_tokens(word + ' ')
                    if temp_tokens + word_tokens > max_tokens:
                        if temp_chunk:
                            chunks.append(' '.join(temp_chunk))
                        temp_chunk = [word]
                        temp_tokens = word_tokens
                    else:
                        temp_chunk.append(word)
                        temp_tokens += word_tokens
                if temp_chunk:
                    current_chunk = temp_chunk
                    current_tokens = temp_tokens
            elif current_tokens + sentence_tokens > max_tokens:
                # Start new chunk with overlap
                chunks.append(' '.join(current_chunk))

                # Calculate overlap - keep last few sentences
                overlap_chunk = []
                overlap_count = 0
                for s in reversed(current_chunk):
                    s_tokens = self.count_tokens(s)
                    if overlap_count + s_tokens <= overlap_tokens:
                        overlap_chunk.insert(0, s)
                        overlap_count += s_tokens
                    else:
                        break

                current_chunk = overlap_chunk + [sentence]
                current_tokens = overlap_count + sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _extract_section_title(self, text: str) -> str | None:
        """Extract section title from markdown-formatted text."""
        # Look for markdown headers
        header_match = re.search(r'^#+\s+(.+?)$', text, re.MULTILINE)
        if header_match:
            return header_match.group(1).strip()

        # Look for bold text at start (often used as headers)
        bold_match = re.search(r'^\*\*(.+?)\*\*', text)
        if bold_match:
            return bold_match.group(1).strip()

        return None

    def process_pdf(
        self,
        file_content: bytes,
        filename: str,
        custom_title: str | None = None,
    ) -> ProcessedDocument:
        """
        Process a PDF file into chunks.

        Args:
            file_content: PDF file bytes
            filename: Original filename
            custom_title: Optional custom title

        Returns:
            ProcessedDocument with chunks and metadata

        Raises:
            ValueError: If document exceeds page limits
        """
        doc_id = str(uuid.uuid4())
        title = custom_title or filename.replace('.pdf', '').replace('_', ' ')

        # Open PDF document
        pdf_stream = BytesIO(file_content)
        doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
        page_count = len(doc)

        # Validate page limit
        if page_count > self.settings.max_pages_per_document:
            doc.close()
            raise ValueError(
                f"Document has {page_count} pages, "
                f"maximum allowed is {self.settings.max_pages_per_document}"
            )

        # Extract to markdown with page chunks using the document object
        md_data = pymupdf4llm.to_markdown(
            doc,
            page_chunks=True,
            write_images=False,
        )

        # Close document after extraction
        doc.close()

        chunks = []
        sections_detected = set()

        for page_data in md_data:
            # Get page number (1-indexed)
            page_metadata = page_data.get("metadata", {})
            page_num = page_metadata.get("page", 0) + 1
            page_text = page_data.get("text", "")

            if not page_text.strip():
                continue

            # Try to detect section title from page content
            section_title = self._extract_section_title(page_text)
            if section_title:
                sections_detected.add(section_title)

            # Split page into chunks
            page_chunks = self._split_into_chunks(
                page_text,
                max_tokens=self.settings.chunk_size_tokens,
                overlap_tokens=self.settings.chunk_overlap_tokens,
            )

            for i, chunk_text in enumerate(page_chunks):
                # Clean up the text
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue

                chunk = Chunk(
                    chunk_id=f"{doc_id}_p{page_num}_c{i}",
                    document_id=doc_id,
                    document_title=title,
                    page_number=page_num,
                    section_title=section_title,
                    text=chunk_text,
                    token_count=self.count_tokens(chunk_text),
                )
                chunks.append(chunk)

        return ProcessedDocument(
            id=doc_id,
            title=title,
            page_count=page_count,
            chunks=chunks,
            sections=list(sections_detected),
            file_size_bytes=len(file_content),
        )

    def validate_file(
        self,
        file_content: bytes,
        filename: str,
    ) -> tuple[bool, str]:
        """
        Validate a PDF file before processing.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return False, "Only PDF files are accepted"

        # Check file size
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > self.settings.max_file_size_mb:
            return False, f"File too large ({size_mb:.1f}MB). Maximum: {self.settings.max_file_size_mb}MB"

        # Try to open as PDF
        try:
            pdf_stream = BytesIO(file_content)
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
            page_count = len(doc)
            doc.close()

            if page_count > self.settings.max_pages_per_document:
                return False, (
                    f"Document has {page_count} pages. "
                    f"Maximum: {self.settings.max_pages_per_document}"
                )

            if page_count == 0:
                return False, "PDF has no pages"

        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"

        return True, "OK"


# Singleton instance
_processor: PDFProcessor | None = None


def get_pdf_processor() -> PDFProcessor:
    """Get or create PDF processor instance."""
    global _processor
    if _processor is None:
        _processor = PDFProcessor()
    return _processor
