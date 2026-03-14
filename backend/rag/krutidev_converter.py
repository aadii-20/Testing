import re

# Character mapping from KrutiDev 010 to Unicode Devanagari
_K2U_MAPPING = [
    ('\xf1', '\u0970'),
    ('Q+Z', 'QZ+'),
    ('sas', 'sa'),
    ('aa', 'a'),
    (')Z', '\u0930\u094d\u0926\u094d\u0927'),
    ('ZZ', 'Z'),
    ('\u2018', '"'),
    ('\u2019', '"'),
    ('\u201c', "'"),
    ('\u201d', "'"),
    ('\xe5', '\u0966'),
    ('\u0192', '\u0967'),
    ('\u201e', '\u0968'),
    ('\u2026', '\u0969'),
    ('\u2020', '\u096a'),
    ('\u2021', '\u096b'),
    ('\u02c6', '\u096c'),
    ('\u2030', '\u096d'),
    ('\u0160', '\u096e'),
    ('\u2039', '\u096f'),
    ('\xb6+', '\u095e\u094d'),
    ('d+', '\u0958'),
    ('[+k', '\u0959'),
    ('[+', '\u0959\u094d'),
    ('x+', '\u095a'),
    ('T+', '\u091c\u093c\u094d'),
    ('t+', '\u095b'),
    ('M+', '\u095c'),
    ('<+', '\u095d'),
    ('Q+', '\u095e'),
    (';+', '\u095f'),
    ('j+', '\u0931'),
    ('u+', '\u0929'),
    ('\xd9k', '\u0924\u094d\u0924'),
    ('\xd9', '\u0924\u094d\u0924\u094d'),
    ('\xe4', '\u0915\u094d\u0924'),
    ('\u2013', '\u0926\u0943'),
    ('\u2014', '\u0915\u0943'),
    ('\xe9', '\u0928\u094d\u0928'),
    ('\u2122', '\u0928\u094d\u0928\u094d'),
    ('=kk', '=k'),
    ('f=k', 'f='),
    ('\xe0', '\u0939\u094d\u0928'),
    ('\xe1', '\u0939\u094d\u092f'),
    ('\xe2', '\u0939\u0943'),
    ('\xe3', '\u0939\u094d\u092e'),
    ('\xbaz', '\u0939\u094d\u0930'),
    ('\xba', '\u0939\u094d'),
    ('\xed', '\u0926\u094d\u0926'),
    ('{k', '\u0915\u094d\u0937'),
    ('{', '\u0915\u094d\u0937\u094d'),
    ('=', '\u0924\u094d\u0930'),
    ('\xab', '\u0924\u094d\u0930\u094d'),
    ('N\xee', '\u091b\u094d\u092f'),
    ('V\xee', '\u091f\u094d\u092f'),
    ('B\xee', '\u0920\u094d\u092f'),
    ('M\xee', '\u0921\u094d\u092f'),
    ('<\xee', '\u0922\u094d\u092f'),
    ('|', '\u0926\u094d\u092f'), # FIXED: 092y to 092f
    ('K', '\u091c\u094d\u091e'),
    ('}', '\u0926\u094d\u0935'),
    ('J', '\u0936\u094d\u0930'),
    ('V\xaa', '\u091f\u094d\u0930'),
    ('M\xaa', '\u0921\u094d\u0930'),
    ('<\xaa\xaa', '\u0922\u094d\u0930'),
    ('N\xaa', '\u091b\u094d\u0930'),
    ('\xd8', '\u0915\u094d\u0930'),
    ('\xde', '\u092b\u094d\u0930'),
    ('nzZ', '\u0930\u094d\u0926\u094d\u0930'),
    ('\xe6', '\u0926\u094d\u0930'),
    ('\xe7', '\u092a\u094d\u0930'),
    ('\xc1', '\u092a\u094d\u0930'),
    ('xz', '\u0917\u094d\u0930'),
    ('#', '\u0930\u0941'),
    (':', '\u0930\u0942'),
    ('v\u2012', '\u0911'),
    ('vks', '\u0913'),
    ('vkS', '\u0914'),
    ('vk', '\u0906'),
    ('v', '\u0905'),
    ('b\xb1', '\u0908\u0902'),
    ('\xc3', '\u0908'),
    ('bZ', '\u0908'),
    ('b', '\u0907'),
    ('m', '\u0909'),
    ('\xc5', '\u090a'),
    (',s', '\u0910'),
    (',', '\u090f'),
    ('_', '\u090b'),
    ('\xf4', '\u0915\u094d\u0915'),
    ('d', '\u0915'),
    ('Dk', '\u0915'),
    ('D', '\u0915\u094d'),
    ('[k', '\u0916'),
    ('[', '\u0916\u094d'),
    ('x', '\u0917'),
    ('Xk', '\u0917'),
    ('X', '\u0917\u094d'),
    ('\xc4', '\u0918'),
    ('?k', '\u0918'),
    ('?', '\u0918\u094d'),
    ('\xb3', '\u0919'),
    ('pkS', '\u091a\u0948'),
    ('p', '\u091a'),
    ('Pk', '\u091a'),
    ('P', '\u091a\u094d'),
    ('N', '\u091b'),
    ('t', '\u091c'),
    ('Tk', '\u091c'),
    ('T', '\u091c\u094d'),
    ('>', '\u091d'),
    ('\xf7', '\u091d\u094d'),
    ('\xa5', '\u091e'),
    ('\xea', '\u091f\u094d\u091f'),
    ('\xeb', '\u091f\u094d\u0920'),
    ('V', '\u091f'),
    ('B', '\u0920'),
    ('\xec', '\u0921\u094d\u0921'),
    ('\xef', '\u0921\u094d\u0922'),
    ('M', '\u0921'),
    ('<', '\u0922'),
    ('.k', '\u0923'),
    ('.', '\u0923\u094d'),
    ('r', '\u0924'),
    ('Rk', '\u0924'),
    ('R', '\u0924\u094d'),
    ('Fk', '\u0925'),
    ('F', '\u0925\u094d'),
    (')', '\u0926\u094d\u0927'),
    ('n', '\u0926'),
    ('/k', '\u0927'),
    ('/', '\u0927\u094d'),
    ('\xcb', '\u0927\u094d'),
    ('\xe8k', '\u0927'),
    ('\xe8', '\u0927'),
    ('u', '\u0928'),
    ('Uk', '\u0928'),
    ('U', '\u0928\u094d'),
    ('i', '\u092a'),
    ('Ik', '\u092a'),
    ('I', '\u092a\u094d'),
    ('Q', '\u092b'),
    ('\xb6', '\u092b\u094d'),
    ('c', '\u092c'),
    ('Ck', '\u092c'),
    ('C', '\u092c\u094d'),
    ('Hk', '\u092d'),
    ('H', '\u092d\u094d'),
    ('e', '\u092e'),
    ('Ek', '\u092e'),
    ('E', '\u092e\u094d'),
    (';', '\u092f'),
    ('\xb8', '\u092f\u094d'),
    ('j', '\u0930'),
    ('y', '\u0932'),
    ('Yk', '\u0932'),
    ('Y', '\u0932\u094d'),
    ('G', '\u0933'),
    ('o', '\u0935'),
    ('Ok', '\u0935'),
    ('O', '\u0935\u094d'),
    ("'k", '\u0936'),
    ("'", '\u0936\u094d'),
    ('"k', '\u0937'),
    ('"', '\u0937\u094d'),
    ('l', '\u0938'),
    ('Lk', '\u0938'),
    ('L', '\u0938\u094d'),
    ('g', '\u0939'),
    ('\xc8', '\u0940\u0902'),
    ('saz', '\u094d\u0930\u0947\u0902'),
    ('z', '\u094d\u0930'),
    ('\xcc', '\u0926\u094d\u0926'),
    ('\xcd', '\u091f\u094d\u091f'),
    ('\xce', '\u091f\u094d\u0920'),
    ('\xcf', '\u0921\u094d\u0921'),
    ('\xd1', '\u0915\u0943'),
    ('\xd2', '\u092d'),
    ('\xd3', '\u094d\u092f'),
    ('\xd4', '\u0921\u094d\u0922'),
    ('\xd6', '\u091d\u094d'),
    ('\xdc', '\u0936\u094d'),
    ('\u201a', '\u0949'),
    ('kas', '\u094b\u0902'),
    ('ks', '\u094b'),
    ('kS', '\u094c'),
    ('\xa1k', '\u093e\u0901'),
    ('k', '\u093e'),
    ('ah', '\u0940\u0902'),
    ('h', '\u0940'),
    ('aq', '\u0941\u0902'),
    ('q', '\u0941'),
    ('aw', '\u0942\u0902'),
    ('\xa1w', '\u0942\u0901'),
    ('w', '\u0942'),
    ('`', '\u0943'),
    ('\u0300', '\u0943'),
    ('as', '\u0947\u0902'),
    ('s', '\u0947'),
    ('aS', '\u0948\u0902'),
    ('S', '\u0948'),
    ('\xaa', '\u094d\u0930'),
    ('a', '\u0902'),
    ('\xa1', '\u0901'),
    ('%', ':'),
    ('W', '\u0945'),
    ('\u2022', '\u093d'),
    ('\xb7', '\u093d'),
    ('~j', '\u094d\u0930'),
    ('~', '\u094d'),
    ('\\', '?'),
    ('+', '\u093c'),
    ('^', '\u2018'),
    ('*', '\u2019'),
    ('\xde', '\u201c'),
    ('\xdf', '\u201d'),
    ('(', ';'),
    ('\xbc', '('),
    ('\xbd', ')'),
    ('\xbe', '='),
    ('A', '\u0964'),
    ('-', '.'),
    ('&', '-'),
]

def krutidev_to_unicode(text: str) -> str:
    if not text:
        return ""

    processed_text = text
    processed_text = processed_text.replace('\xa0', ' ')

    temp_text = processed_text
    
    # Pre-process i-matra reordering to avoid collision with mapped characters
    # f + ? -> ? + ि
    # Note: We use \g<1> for group reference and literal unicode chars to avoid 'bad escape \u' in re.sub
    temp_text = re.sub(r'fa(.)', '\g<1>\u093f\u0902', temp_text)
    temp_text = re.sub(r'f(.)', '\g<1>\u093f', temp_text)
    
    # Now map other characters
    for kru, uni in _K2U_MAPPING:
        temp_text = temp_text.replace(kru, uni)

    # Reph logic: ?Z -> र्?
    # ?Z -> र + ् + ?
    temp_text = re.sub(r'(.)Z', '\u0930\u094d\g<1>', temp_text)

    # Final cleanup
    temp_text = temp_text.replace('~', '\u094d')
    
    return temp_text

def is_krutidev(text: str) -> bool:
    """
    Stricter heuristic to detect KrutiDev 010 encoding.
    English text frequently contains 'f', 'k', 'l', so we look for 
    sequences that are extremely common in Hindi but rare in English.
    """
    if not text:
        return False
        
    # 1. If it already has Devanagari, it's already Unicode.
    hindi_chars = len([c for c in text[:1000] if '\u0900' <= c <= '\u097F'])
    if hindi_chars > 50:
        return False
        
    # 2. Check for signature KrutiDev "garbage" sequences.
    # NCERT PDFs use these constantly:
    # x| (ग), [k (ख), Dk (क), /k (ध), Hk (भ), Yk (ल), Ok (व), Lk (स), 'k (श)
    # These are very rare in standard English prose.
    kruti_signatures = [
        r'x\|', r'\[k', r'Dk', r'Fk', r'Hk', r'Yk', r'Ok', r'Lk', r'/k', r'\'k', r'\"k',
        r'vk', r'vks', r'vkS', r'dk', r'ik', r'ek', r'uk', r'rk'
    ]
    
    score = 0
    sample = text[:2000] # Check a larger sample
    for sig in kruti_signatures:
        if re.search(sig, sample):
            score += 1
            
    # If we find 3+ distinct Kruti signatures, it's almost certainly KrutiDev
    if score >= 3:
        return True
        
    return False
