"""
Diagnostic script to test PDF parsing for all std/9 subjects/chapters.
Outputs results to a UTF-8 encoded text file.
"""
import os
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rag.pdf_loader import load_pdf_text, chunk_text

STD_DIR = Path(__file__).parent.parent / "std"
OUTPUT_FILE = Path(__file__).parent / "diagnose_output.txt"

def has_devanagari(text: str) -> bool:
    for ch in text:
        try:
            if "DEVANAGARI" in unicodedata.name(ch, ""):
                return True
        except ValueError:
            pass
    return False

def count_devanagari(text: str) -> int:
    count = 0
    for ch in text:
        try:
            if "DEVANAGARI" in unicodedata.name(ch, ""):
                count += 1
        except ValueError:
            pass
    return count

def diagnose_standard(standard: str, out):
    std_path = STD_DIR / standard
    if not std_path.exists():
        out.write(f"ERROR: std/{standard} directory not found at {std_path}\n")
        return

    out.write(f"\n{'='*80}\n")
    out.write(f"  DIAGNOSTIC REPORT FOR STANDARD {standard}\n")
    out.write(f"{'='*80}\n")

    subjects = sorted([d for d in std_path.iterdir() if d.is_dir()])
    out.write(f"\nFound {len(subjects)} subjects: {[s.name for s in subjects]}\n")

    total_issues = 0

    for subject_path in subjects:
        subject_name = subject_path.name
        pdfs = sorted(subject_path.glob("*.pdf"))

        out.write(f"\n{'_'*60}\n")
        out.write(f"  Subject: {subject_name} ({len(pdfs)} chapters)\n")
        out.write(f"{'_'*60}\n")

        for pdf_path in pdfs:
            chapter_name = pdf_path.stem
            file_size_kb = pdf_path.stat().st_size / 1024

            out.write(f"\n  {chapter_name}.pdf ({file_size_kb:.0f} KB)\n")

            try:
                raw_text = load_pdf_text(str(pdf_path))
                text_length = len(raw_text)
                word_count = len(raw_text.split())
                chunks = chunk_text(raw_text)
                num_chunks = len(chunks)

                out.write(f"     Text length: {text_length} chars, {word_count} words\n")
                out.write(f"     Chunks created: {num_chunks}\n")

                if text_length < 100:
                    out.write(f"     ISSUE: Very little text extracted! Possible image-based PDF\n")
                    total_issues += 1
                elif word_count < 50:
                    out.write(f"     ISSUE: Very few words extracted ({word_count})\n")
                    total_issues += 1
                else:
                    out.write(f"     OK: Text extraction successful\n")

                # Check for Devanagari if Hindi
                if subject_name.lower() == "hindi":
                    dev_count = count_devanagari(raw_text)
                    dev_ratio = dev_count / max(text_length, 1)
                    out.write(f"     Devanagari chars: {dev_count} ({dev_ratio:.1%} of text)\n")
                    if dev_count < 50:
                        out.write(f"     ISSUE: Hindi PDF has very few Devanagari characters!\n")
                        out.write(f"        This suggests pdfplumber cannot extract Hindi text properly.\n")
                        total_issues += 1
                    else:
                        out.write(f"     OK: Hindi text (Devanagari) extraction successful\n")

                # Show sample text (first 300 chars)
                sample = raw_text[:300].replace('\n', ' ').strip()
                out.write(f"     Sample: {sample[:250]}\n")

                # Check if chunks are meaningful
                if num_chunks > 0:
                    avg_chunk_len = sum(len(c) for c in chunks) / num_chunks
                    empty_chunks = sum(1 for c in chunks if len(c.strip()) < 10)
                    out.write(f"     Avg chunk length: {avg_chunk_len:.0f} chars\n")
                    if empty_chunks > 0:
                        out.write(f"     ISSUE: {empty_chunks} nearly-empty chunks found\n")
                        total_issues += 1

            except Exception as e:
                out.write(f"     ERROR: {e}\n")
                total_issues += 1

    out.write(f"\n{'='*80}\n")
    out.write(f"  SUMMARY: {total_issues} issues found\n")
    out.write(f"{'='*80}\n")

if __name__ == "__main__":
    standard = sys.argv[1] if len(sys.argv) > 1 else "9"
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        diagnose_standard(standard, f)
    print(f"Diagnostic output written to {OUTPUT_FILE}")
