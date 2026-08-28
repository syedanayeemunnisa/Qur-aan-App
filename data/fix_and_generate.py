"""Fix Roman Urdu generator post-processing and run full generation."""

import sys
import json
import re
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from roman_urdu_generator import RomanUrduGenerator, generate_dataset_roman_urdu

logging.basicConfig(level=logging.INFO)

# ── Monkey-patch the _post_process method ──────────────────────────

@staticmethod
def improved_post_process(text):
    """Improved post-processing for Roman Urdu."""
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # Space before punctuation
    text = re.sub(r'\s+([.,!?;:)\]\)])', r'\1', text)
    text = re.sub(r'([\(\[{])\s+', r'\1', text)
    
    # Clean empty quotes/apostrophes
    text = text.replace("''", "")
    text = text.replace("'' '", "' ")
    text = text.replace("' '", " ")
    
    # Fix 'o' at word start -> 'w' (wao at start of word = consonant)
    text = re.sub(r'\bo([aâeiou])', lambda m: 'w' + m.group(1), text, flags=re.IGNORECASE)
    
    # Fix 'o' between two consonants -> 'u'
    # This handles cases like شروع (shuru), خوب (khoob)
    text = re.sub(r'([bcdfghjklmnpqrstvxz])o([bcdfghjklmnpqrstvxz])', 
                  r'\1u\2', text, flags=re.IGNORECASE)
    
    # Fix 'y' between two consonants -> 'i'
    # This handles cases like پیدا (paida)
    text = re.sub(r'([bcdfghjklmnpqrstvxz])y([bcdfghjklmnpqrstvxz])',
                  r'\1i\2', text, flags=re.IGNORECASE)
    
    # Fix 'e' at the end of some words -> 'ay'
    # e.g., "اچھال" -> "acha", but "اچھے" should remain "achay"
    # 'ny' at word end -> 'ne'
    text = re.sub(r'\bky\b', 'kya', text)
    text = re.sub(r'\bny\b', 'ne', text)
    
    # Fix Specific known problematic words
    word_fixes = {
        r'\bShro\b': 'Shuru',
        r'\bshro\b': 'shuru',
        r'\bKhb\b': 'Khoob',
        r'\bkhb\b': 'khoob',
        r'\bMdd\b': 'Madad',
        r'\bmdd\b': 'madad',
        r'\bPyda\b': 'Paida',
        r'\bpyda\b': 'paida',
        r'\bHmsr\b': 'Hamsar',
        r'\bhmsr\b': 'hamsar',
        r'\bNyaz\b': 'Niyaz',
        r'\bnyaz\b': 'niyaz',
        r'\btryf\b': 'tareef',
        r'\bTryf\b': 'Tareef',
    }
    
    # Replace تعالیٰ variants
    text = re.sub(r'\btaala\b', "ta'ala", text, flags=re.IGNORECASE)
    text = re.sub(r'\btali\b', "ta'ala", text, flags=re.IGNORECASE)
    text = re.sub(r'\btaly\b', "ta'ala", text, flags=re.IGNORECASE)
    
    # Apply specific word fixes
    for pattern, replacement in word_fixes.items():
        text = re.sub(pattern, replacement, text)
    
    # Final: ensure word-boundary 'h' after consonants is not separated
    # e.g., 'k h' -> 'kh'
    text = re.sub(r'([bcdfgjklmnpqrstvxz])\s+h\b', r'\1h', text)
    
    # Capitalize first letter of text
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
    
    return text.strip()


# Apply the fix
RomanUrduGenerator._post_process = staticmethod(improved_post_process)

# ── Test on sample verses ──────────────────────────────────────────

print("=" * 60)
print("TESTING IMPROVED ROMAN URDU GENERATOR")
print("=" * 60)

data_path = Path(__file__).resolve().parent / "quran_dataset.json"
data = json.load(open(data_path, "r", encoding="utf-8"))

generator = RomanUrduGenerator()

# Test specific verses
test_verses = [0, 1, 2, 3, 4]  # Surah 1 (Al-Fatiha)
# Add Surah 112 verses
for i, v in enumerate(data):
    if v['surah'] == 112:
        test_verses.append(i)

for idx in test_verses:
    v = data[idx]
    old_roman = v.get('roman', '')
    new_roman = generator.convert(v['urdu'])
    print(f"\n{v['verse_key']}:")
    print(f"  OLD: {old_roman[:100]}")
    print(f"  NEW: {new_roman[:100]}")

# ── Ask for confirmation before full generation ────────────────────

print("\n" + "=" * 60)
print("Ready to generate Roman Urdu for all 6,236 verses.")
print("A backup will be created before updating.")

# Run full generation
summary = generate_dataset_roman_urdu(data_path, data_path)
print("\n" + summary)
