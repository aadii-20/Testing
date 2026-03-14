import re
import fitz  # PyMuPDF
from typing import List

def _deduplicate_overlapping_text(text: str) -> str:
    """
    Fixes cases where text is extracted multiple times due to PDF layering.
    Handles both character repetition and phrase repetition.
    """
    if not text:
        return ""

    # 1. Fix character repetition (e.g., 'NNNNNooooo')
    text = re.sub(r'(.)\1{4,}', lambda m: m.group(1), text)
    
    # 2. Fix phrase/line repetition (e.g., 'Notes for the T Notes for the T')
    # We look for large chunks of text that repeat exactly.
    # Split into lines and deduplicate adjacent identical lines
    lines = text.split('\n')
    cleaned_lines = []
    for i in range(len(lines)):
        line = lines[i].strip()
        if not line:
            cleaned_lines.append("")
            continue
            
        # If this line is a significant prefix of the next line or vice versa
        # Or if it's just identical
        if i > 0 and line == cleaned_lines[-1].strip():
            continue
            
        cleaned_lines.append(lines[i])
        
    text = '\n'.join(cleaned_lines)
    
    # 3. Handle the 'staggered' overlap (N o t e s N o t e s)
    # This is harder to catch with regex without breaking real words.
    # We'll rely on checking for repeating substrings.
    for _ in range(3): # Multi-pass for nested repeats
        text = re.sub(r'(.{10,200}?)\1+', r'\1', text)

    return text

from rag import krutidev_converter

def load_pdf_text(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    Handles legacy font encodings by extracting blocks and cleaning positioning noise.
    """
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # We use "blocks" to get text in discrete chunks
            # This helps distinguish overlapping blocks vs continuous text
            blocks = page.get_text("blocks")
            # Sort blocks by vertical then horizontal position
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            last_block_text = ""
            for b in blocks:
                block_text = b[4].strip()
                if not block_text:
                    continue
                
                # If this block is identical to the last one (overlapping), skip it
                if block_text == last_block_text:
                    continue
                
                text += block_text + "\n"
                last_block_text = block_text
            text += "\n" # Page break
        doc.close()
    except Exception as e:
        print(f"WARNING: PyMuPDF extraction failed for {pdf_path}: {e}")
        return ""

    # Clean up any remaining duplication artifacts
    text = _deduplicate_overlapping_text(text)
    
    # --- New: KrutiDev handling ---
    # Detect if the extracted text looks like KrutiDev garble (ASCII mapping)
    if krutidev_converter.is_krutidev(text):
        print(f"INFO: Detected KrutiDev encoding in {pdf_path}. Converting to Unicode...")
        text = krutidev_converter.krutidev_to_unicode(text)
    
    return text

def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """
    Splits text into chunks of roughly max_tokens size.
    Uses character count as a simple proxy for tokens.
    """
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    current_chars = 0

    for word in words:
        current.append(word)
        current_chars += len(word) + 1 # +1 for space
        if current_chars >= max_tokens:
            chunks.append(" ".join(current))
            current = []
            current_chars = 0

    if current:
        chunks.append(" ".join(current))

    return chunks
