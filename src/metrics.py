import math
from collections import Counter

from src.ciphers import ALPHABET


def entropy(text: str) -> float:
    counts = Counter(text)
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def avalanche(last_plain: str, last_cipher: str, encrypt) -> float:
    """Change the last plaintext character, re-encrypt, and return the
    percentage of ciphertext characters that differ."""
    idx = ALPHABET.index(last_plain[-1])
    modified = last_plain[:-1] + ALPHABET[(idx + 1) % 27]
    modified_cipher = encrypt(modified)

    diff = sum(a != b for a, b in zip(last_cipher, modified_cipher))
    diff += abs(len(last_cipher) - len(modified_cipher))
    return diff / max(len(last_cipher), len(modified_cipher)) * 100


def validate(plaintexts: list[str], ciphertexts: list[str], encrypt):
    """Returns ([entropy_plain, entropy_cipher], avalanche_pct)."""
    ent = [entropy("".join(plaintexts)), entropy("".join(ciphertexts))]
    return ent, avalanche(plaintexts[-1], ciphertexts[-1], encrypt)
