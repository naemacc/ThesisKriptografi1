# Penggunaan:
#   python experiments/run.py            -> jalankan semua kombinasi
#   python experiments/run.py sc x       -> scale + cross
# Alias: sc=scale, se=sense, x=cross, q=sequenced

import argparse
import sys
from pathlib import Path

# Tambahkan folder induk ke sys.path agar config dan src dapat diimpor
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import CATEGORIES, N_ITERATIONS, PROCESSED_DIR, RUNS_DIR
from src.ciphers import CIPHERS, char_test
from src.io_utils import (
    append_log,
    load_dataset,
    new_run_dir,
    save_category,
    save_json,
)
from src.metrics import validate

ALIASES = {"sc": "scale", "se": "sense", "x": "cross", "q": "sequenced"}


def print_progress(i, total):
    step = max(1, total // 100)
    if i % step == 0 or i == total:
        print(
            f"  Progress: {i / total * 100:.0f}% ({i}/{total})",
            end="\r",
            flush=True,
        )


# Hanya proses enkripsi yang diukur waktunya
def encrypt_all(sentences, encrypt):
    import time

    ciphertexts, times = [], []
    total = len(sentences)
    for i, sentence in enumerate(sentences, start=1):
        t0 = time.perf_counter()
        enc = encrypt(sentence)
        times.append(time.perf_counter() - t0)
        ciphertexts.append(enc)
        print_progress(i, total)
    print()
    return ciphertexts, times


# Verifikasi dilakukan terpisah dari pengukuran waktu.
# Kegagalan dicatat, tidak menghentikan program, agar jumlahnya terlihat.
def verify_all(category, total_file, sentences, ciphertexts, decrypt):
    gagal = []
    for i, (plain, enc) in enumerate(zip(sentences, ciphertexts), start=1):
        dec = decrypt(enc)
        if dec != plain:
            gagal.append({"index": i, "plaintext": plain, "hasil_dekripsi": dec})

    n = len(sentences)
    return {
        "kategori": category,
        "total_di_file": total_file,
        "total_diproses": n,
        "jumlah_sesuai": total_file == n,
        "berhasil": n - len(gagal),
        "gagal": len(gagal),
        "akurasi_pct": round((n - len(gagal)) / n * 100, 4) if n else 0,
        "contoh_gagal": gagal[:5],  # maksimal 5 agar file tetap kecil
    }


def summarize_verification(scenario, method, iteration, stamp, verifs, uji_char):
    total_n = sum(v["total_diproses"] for v in verifs)
    total_ok = sum(v["berhasil"] for v in verifs)
    return {
        "skenario": scenario,
        "metode": method,
        "iterasi": iteration,
        "waktu": stamp,
        "total_kalimat": total_n,
        "total_berhasil": total_ok,
        "total_gagal": total_n - total_ok,
        "akurasi_total_pct": round(total_ok / total_n * 100, 4) if total_n else 0,
        "per_kategori": verifs,
        "uji_karakter": uji_char,
    }


def run_category(category, data, encrypt, decrypt, out_dir):
    total_file, sentences = data

    ciphertexts, times = encrypt_all(sentences, encrypt)
    verif = verify_all(category, total_file, sentences, ciphertexts, decrypt)
    ent, aval = validate(sentences, ciphertexts, encrypt)

    print(
        f"  Entropy: {ent[0]:.4f} (plain), {ent[1]:.4f} (cipher), Avalanche: {aval:.2f}%"
    )
    print(f"  Total: {sum(times):.6f} s")
    print(
        f"  Verifikasi: {verif['berhasil']}/{verif['total_diproses']} ({verif['akurasi_pct']}%)"
    )
    if verif["gagal"]:
        print(f"  [PERINGATAN] {verif['gagal']} kalimat gagal diverifikasi!")

    save_category(out_dir, category, ciphertexts, times, ent, aval)
    append_log(
        out_dir / "log.json",
        {
            "category": category,
            "n": len(times),
            "total_time_s": sum(times),
            "entropy_plain": ent[0],
            "entropy_cipher": ent[1],
            "avalanche_pct": aval,
        },
    )
    return verif


def run_iteration(scenario, method, iteration, datasets, uji_char):
    encrypt, decrypt = CIPHERS[method]
    out_dir = new_run_dir(RUNS_DIR / scenario / method)

    print(f"Iterasi ke-{iteration} ({scenario}/{method})")
    verifs = []
    for cat, data in datasets.items():
        print(f"Memproses kategori: {cat}")
        verifs.append(run_category(cat, data, encrypt, decrypt, out_dir))

    ringkasan = summarize_verification(
        scenario, method, iteration, out_dir.name, verifs, uji_char
    )
    save_json(out_dir / "verification.json", ringkasan)


def run_experiment(scenario, method):
    encrypt, decrypt = CIPHERS[method]

    datasets = {
        c: load_dataset(PROCESSED_DIR / scenario / f"{c}.json")
        for c in CATEGORIES[scenario]
    }
    uji_char = char_test(encrypt, decrypt)

    for it in range(1, N_ITERATIONS + 1):
        run_iteration(scenario, method, it, datasets, uji_char)


def resolve(value, choices, parser):
    value = ALIASES.get(value, value)
    if value == "all":
        return list(choices)
    if value not in choices:
        parser.error(
            f"'{value}' tidak valid. Pilihan: {', '.join(choices)}, all "
            f"(alias: {', '.join(f'{k}={v}' for k, v in ALIASES.items())})"
        )
    return [value]


def main():
    parser = argparse.ArgumentParser(
        description="Jalankan eksperimen enkripsi. Alias: sc=scale, se=sense, x=cross, q=sequenced"
    )
    parser.add_argument("scenario", nargs="?", default="all")
    parser.add_argument("method", nargs="?", default="all")
    args = parser.parse_args()

    scenarios = resolve(args.scenario, CATEGORIES.keys(), parser)
    methods = resolve(args.method, CIPHERS.keys(), parser)

    for scenario in scenarios:
        for method in methods:
            run_experiment(scenario, method)


if __name__ == "__main__":
    main()
