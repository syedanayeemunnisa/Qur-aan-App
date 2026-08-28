"""Integrate the improved _post_process method into roman_urdu_generator.py."""

import re
from pathlib import Path

# Read the generator file
path = Path(__file__).resolve().parent / "roman_urdu_generator.py"
content = path.read_text("utf-8")

# Find the _post_process method - look for its signature
old_start = 'def _post_process(self, text: str) -> str:'
old_end = 'def _fix_common_words'

idx_start = content.find(old_start)
idx_end = content.find(old_end, idx_start)

if idx_start == -1 or idx_end == -1:
    print("ERROR: Could not find _post_process method boundaries")
    # Try to find the end differently
    idx_end = content.find('\n    # ═══════════════════════════════════', idx_start)
    
if idx_start == -1:
    print("FATAL: Could not find _post_process method")
    exit(1)

old_method = content[idx_start:idx_end]

new_method = '''    def _post_process(self, text: str) -> str:
        """Final post-processing for readability."""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)

        # Space before punctuation
        text = re.sub(r'\\s+([.,!?;:\\)\\]]+)', r'\\1', text)
        text = re.sub(r'([\\(\\[{])\\s+', r'\\1', text)

        # Clean up empty quotes/apostrophes
        text = text.replace("''", '')

        # Fix 'oh' → 'woh' (standalone word وہ)
        text = re.sub(r'\\boh\\b', 'woh', text, flags=re.IGNORECASE)

        # Fix 'o' at start of word → 'w' (Urdu و at start = consonant 'w')
        text = re.sub(r'\\bo([aâeiou])', lambda m: 'w' + m.group(1), text, flags=re.IGNORECASE)

        # Fix 'o' between two consonants → 'u'
        text = re.sub(r'([bcdfghjklmnpqrstvxz])o([bcdfghjklmnpqrstvxz])',
                      r'\\1u\\2', text, flags=re.IGNORECASE)

        # Fix 'y' between consonants → 'i' for readability
        text = re.sub(r'([bcdfghjklmnpqrstvxz])y([bcdfghjklmnpqrstvxz])',
                      r'\\1i\\2', text, flags=re.IGNORECASE)

        # Fix 'w' between two consonants → 'u'
        text = re.sub(r'([bcdfghjklmnpqrstvxz])w([bcdfghjklmnpqrstvxz])',
                      r'\\1u\\2', text, flags=re.IGNORECASE)

        # Common word-specific fixes
        text = re.sub(r'\\bShro\\b', 'Shuru', text)
        text = re.sub(r'\\bshro\\b', 'shuru', text)
        text = re.sub(r'\\bkhob\\b', 'khoob', text, flags=re.IGNORECASE)
        text = re.sub(r'\\bnyaz\\b', 'niyaz', text, flags=re.IGNORECASE)
        text = re.sub(r"\\btaala\\b", "ta'ala", text, flags=re.IGNORECASE)
        text = re.sub(r"\\btali\\b", "ta'ala", text, flags=re.IGNORECASE)

        # Fix common short words
        text = re.sub(r'\\bky\\b', 'kya', text)
        text = re.sub(r'\\bny\\b', 'ne', text)
        text = re.sub(r'\\bpy\\b', 'pe', text)
        text = re.sub(r'\\bty\\b', 'te', text)

        # Capitalize first letter of text
        if text and text[0].isalpha():
            text = text[0].upper() + text[1:]

        return text.strip()

'''

# Replace
content = content.replace(old_method, new_method)

# Write back
path.write_text(content, "utf-8")

print(f"SUCCESS: Replaced _post_process method")
print(f"Old method was {len(old_method)} chars")
print(f"New method is {len(new_method)} chars")

# Verify by importing
import sys
sys.path.insert(0, str(path.parent))
from roman_urdu_generator import RomanUrduGenerator
generator = RomanUrduGenerator()
# Test
test_result = generator.convert("آپ کہہ دیجئے کہ وہ اللہ تعالیٰ ایک ہے")
print(f"Test: {test_result}")
