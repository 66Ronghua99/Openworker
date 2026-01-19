import re
from typing import List

class RecursiveTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ".", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Split text into chunks aiming for chunk_size."""
        final_chunks = []
        good_splits = self._split_text_recursive(text, self.separators)
        
        # Merge splits into chunks of correct size
        current_chunk = ""
        for split in good_splits:
            if len(current_chunk) + len(split) < self.chunk_size:
                current_chunk += split
            else:
                if current_chunk:
                    final_chunks.append(current_chunk)
                # Apply overlap involves keeping tail of prev chunk - simplified here for brevity
                # Real implementation would use a deque or sliding window.
                # Here we just start fresh or use current split if it fits.
                current_chunk = split
        
        if current_chunk:
            final_chunks.append(current_chunk)
            
        return final_chunks

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using the first valid separator.
        """
        if not separators:
            return [text] # Base case: no more separators, return as is (might be too long, but can't split further)

        separator = separators[0]
        new_separators = separators[1:]

        # If separator is empty string, every char is a split
        if separator == "":
            return list(text)

        if separator in text:
            splits = text.split(separator)
            # Re-attach separator to the end of each split (except the last one if you want) or keep it loose.
            # To reconstruct sentences, usually you want keeping it. 
            # Simple approach: split and process.
            final_splits = []
            for s in splits:
                if not s: continue 
                if len(s) > self.chunk_size: # If this piece is still too big, recurse
                     final_splits.extend(self._split_text_recursive(s, new_separators))
                else:
                    final_splits.append(s + separator) # Add separator back approximation
            return final_splits
        else:
            return self._split_text_recursive(text, new_separators)
