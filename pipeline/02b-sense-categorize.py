import json
import os
import time

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, "../data/interim/cleaned")
output_dir = os.path.join(SCRIPT_DIR, "../data/interim/sense-categorized")

# Buat folder output jika belum ada
os.makedirs(output_dir, exist_ok=True)

# Kategori pengelompokan berdasarkan jumlah kata menggunakan set() untuk menghindari duplikasi pada list hasil
categories = {"pendek": set(), "menengah": set(), "panjang": set()}


# Cetak progress per 1% pada baris yang sama
def print_progress(i, total):
    step = max(1, total // 100)
    if i % step == 0 or i == total:
        print(
            f"    Progress: {i / total * 100:.0f}% ({i}/{total})", end="\r", flush=True
        )


start_all = time.perf_counter()
files = [f for f in os.listdir(input_dir) if f.endswith(".json")]  # File .JSON saja
print(f"Ditemukan {len(files)} file JSON di: {input_dir}")

# Iterasi setiap file JSON di folder input
for n, file in enumerate(files, start=1):
    print(f"[{n}/{len(files)}] Membaca {file!r} ...")
    filepath = os.path.join(input_dir, file)
    try:
        # Baca file JSON
        with open(filepath, "r", encoding="utf-8") as input_file:
            data = json.load(input_file)
    except Exception as e:
        print(f"  Error membaca {file!r}: {e}")
        continue

    sentences = data.get("data", [])
    total = len(sentences)
    di_luar_rentang = 0

    # Iterasi setiap kalimat dalam data
    for i, sentence in enumerate(sentences, start=1):
        word_count = len(sentence.split())

        # Tentukan kategori berdasarkan jumlah kata
        if 1 <= word_count <= 30:
            categories["pendek"].add(sentence)
        elif 31 <= word_count <= 60:
            categories["menengah"].add(sentence)
        elif 61 <= word_count <= 100:
            categories["panjang"].add(sentence)
        else:
            di_luar_rentang += 1
        print_progress(i, total)
    print()

    status = ", ".join(f"{k}: {len(v)}" for k, v in categories.items())
    print(f"  Dibuang (di luar 1-100 kata): {di_luar_rentang}")
    print(f"  Total sementara -> {status}")

# Simpan hasil pengelompokan ke file terpisah per kategori
print("Menyimpan hasil pengelompokan ...")
for category, lines in categories.items():
    print(f"  Mengurutkan dan menyimpan '{category}' ({len(lines)} kalimat) ...")

    # Urutkan kalimat agar konsisten
    sorted_lines = sorted(list(lines))

    # Hitung jumlah kata per kalimat
    word_counts = []
    for line in sorted_lines:
        count = len(line.split())
        word_counts.append(count)

    # Buat data ringkasan + isi dalam format JSON
    if word_counts:
        min_words = min(word_counts)
        max_words = max(word_counts)
    else:
        min_words = 0
        max_words = 0

    output_data = {
        "min_words": min_words,
        "max_words": max_words,
        "total": len(sorted_lines),
        "data": sorted_lines,
    }

    # Simpan hasil ke file JSON
    output_path = os.path.join(output_dir, f"{category.lower()}.json")
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2, ensure_ascii=False)

print(f"Selesai dalam {time.perf_counter() - start_all:.1f} detik.")
print("Hasil pengelompokan disimpan di:", output_dir)
