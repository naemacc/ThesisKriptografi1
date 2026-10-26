# Alfabet dan spasi (total 27 karakter)
ALPHABET = "abcdefghijklmnopqrstuvwxyz "


def _rot13(char):
    return ALPHABET[(ALPHABET.index(char) + 13) % 27]


def _rot13_inv(char):
    return ALPHABET[(ALPHABET.index(char) - 13) % 27]


# Atbash adalah kebalikan dirinya sendiri, jadi tidak perlu fungsi inversi
def _atbash(char):
    return ALPHABET[(25 - ALPHABET.index(char)) % 27]


def _apply(string, even, odd):
    return "".join(even(c) if i % 2 == 0 else odd(c) for i, c in enumerate(string))


# Skema silang: posisi genap pakai ROT13, posisi ganjil pakai Atbash
def cross_encrypt(string):
    return _apply(string, _rot13, _atbash)


def cross_decrypt(string):
    return _apply(string, _rot13_inv, _atbash)


# Skema berurutan: ROT13 lalu Atbash pada setiap karakter
def sequenced_encrypt(string):
    return "".join(_atbash(_rot13(c)) for c in string)


def sequenced_decrypt(string):
    return "".join(_rot13_inv(_atbash(c)) for c in string)


# Uji seluruh 27 karakter pada posisi genap dan ganjil.
# Cipher substitusi valid jika pemetaannya bijektif dan dapat didekripsi.
def char_test(encrypt, decrypt):
    hasil = {}
    for pos, nama in ((0, "genap"), (1, "ganjil")):
        pemetaan = {}
        sesuai = True
        for c in ALPHABET:
            plain = "a" * pos + c
            enc = encrypt(plain)
            pemetaan[c] = enc[pos]
            sesuai = sesuai and decrypt(enc) == plain

        unik = len(set(pemetaan.values()))
        hasil[f"posisi_{nama}"] = {
            "karakter_diuji": len(ALPHABET),
            "hasil_unik": unik,
            "bijektif": unik == len(ALPHABET),
            "dekripsi_sesuai": sesuai,
            "pemetaan": pemetaan,
        }
    return hasil


CIPHERS = {
    "cross": (cross_encrypt, cross_decrypt),
    "sequenced": (sequenced_encrypt, sequenced_decrypt),
}
