import re
from typing import List, Dict, Any


class TextChunker:
    """Intelligently cleans and splits extracted text into overlapping semantic chunks."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize whitespace, remove unprintable chars while preserving structure."""
        if not text:
            return ""
        # Remove non-printable characters except newlines/tabs
        cleaned = re.sub(r"[^\x20-\x7E\n\t]", " ", text)
        # Normalize multiple spaces and tabs to single space
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        # Normalize 3+ newlines to 2 newlines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def chunk_extracted_sections(self, extracted_sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a list of extracted sections/pages into chunks with metadata.
        Each returned item has:
        {
            "chunk_index": int,
            "chunk_text": str,
            "page_number": int or None,
            "section_title": str or None,
            "token_count": int
        }
        """
        all_chunks = []
        chunk_counter = 0

        for section in extracted_sections:
            raw_text = section.get("text", "")
            page_number = section.get("page_number")
            section_title = section.get("section_title")
            cleaned = self.clean_text(raw_text)

            if not cleaned:
                continue

            section_chunks = self._split_text_into_chunks(cleaned)
            for chunk_str in section_chunks:
                # Approximate token count (~4 characters per token in English)
                token_count = max(1, len(chunk_str.split()))

                all_chunks.append({
                    "chunk_index": chunk_counter,
                    "chunk_text": chunk_str,
                    "page_number": page_number,
                    "section_title": section_title,
                    "token_count": token_count
                })
                chunk_counter += 1

        return all_chunks

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text with overlap, preferring sentence boundaries."""
        if len(text) <= self.chunk_size:
            return [text]

        # Split on sentence boundaries
        sentence_pattern = r"(?<=[.?!])\s+"
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sen_len = len(sentence)

            # If a single sentence is huge, chunk it by words
            if sen_len > self.chunk_size:
                if current_chunk:
                    chunk_text = " ".join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                    current_chunk = []
                    current_len = 0

                words = sentence.split(" ")
                word_chunk = []
                word_len = 0
                for w in words:
                    word_chunk.append(w)
                    word_len += len(w) + 1
                    if word_len >= self.chunk_size:
                        chunks.append(" ".join(word_chunk))
                        # Keep overlap
                        overlap_words = word_chunk[-max(1, int(self.chunk_overlap / 6)):]
                        word_chunk = list(overlap_words)
                        word_len = sum(len(x) + 1 for x in word_chunk)

                if word_chunk:
                    current_chunk = word_chunk
                    current_len = word_len
                continue

            if current_len + sen_len + 1 > self.chunk_size:
                # Flush current chunk
                chunk_str = " ".join(current_chunk).strip()
                if chunk_str:
                    chunks.append(chunk_str)

                # Keep overlap sentences from the tail of current_chunk
                overlap_chunk = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) + 1 <= self.chunk_overlap:
                        overlap_chunk.insert(0, s)
                        overlap_len += len(s) + 1
                    else:
                        break

                current_chunk = list(overlap_chunk)
                current_len = sum(len(s) + 1 for s in current_chunk)

            current_chunk.append(sentence)
            current_len += sen_len + 1

        if current_chunk:
            final_str = " ".join(current_chunk).strip()
            if final_str and (not chunks or final_str != chunks[-1]):
                chunks.append(final_str)

        return chunks
