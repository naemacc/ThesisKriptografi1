import json
import os
import random
import time

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, "../data/interim/cleaned")
output_dir = os.path.join(SCRIPT_DIR, "../data/processed/scale")
os.makedirs(output_dir, exist_ok=True)

LIMITS = {"sedikit": 100000, "sedang": 500000, "banyak": 1000000}


# Cetak progress per 1% pada baris yang sama
def print_progress(i, total):
    step = max(1, total // 100)
    if i % step == 0 or i == total:
        print(
            f"    Progress: {i / total * 100:.0f}% ({i}/{total})", end="\r", flush=True
        )


def get_all_data():
    all_data = []
    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    for n, file in enumerate(files, start=1):
        print(f"[{n}/{len(files)}] Membaca {file!r} ...")
        with open(os.path.join(input_dir, file), "r", encoding="utf-8") as file_input:
            all_data.extend(json.load(file_input)["data"])

    print(f"Total sebelum deduplikasi: {len(all_data)}")
    print("Menghapus duplikat ...")
    return list(set(all_data))


def generate_target_data(source_pool: list, target_count: int):
    result = source_pool[: min(len(source_pool), target_count)]
    random.shuffle(source_pool)  # Acak data sumber untuk variasi

    asli = len(result)
    print(f"  Data asli dipakai: {asli}, perlu augmentasi: {target_count - asli}")

    # Augmentasi jika data kurang dari target
    while len(result) < target_count:
        result.append(f"{random.choice(source_pool)} {random.choice(source_pool)}")
        print_progress(len(result), target_count)

    if asli < target_count:
        print()
    return result[:target_count]


start_all = time.perf_counter()

# List utama semua data
all_sentences = get_all_data()
print(f"Total data unik ditemukan: {len(all_sentences)}")

for n, (category, limit) in enumerate(LIMITS.items(), start=1):
    print(f"[{n}/{len(LIMITS)}] Membuat kategori '{category}' (target {limit})")
    final_data = generate_target_data(all_sentences, limit)

    print("  Menghitung jumlah kata ...")
    word_counts = [len(line.split()) for line in final_data]
    output_data = {
        "min_words": min(word_counts) if word_counts else 0,
        "max_words": max(word_counts) if word_counts else 0,
        "total": len(final_data),
        "data": final_data,
    }

    print("  Menyimpan file ...")
    with open(
        os.path.join(output_dir, f"{category}.json"), "w", encoding="utf-8"
    ) as file_output:
        json.dump(output_data, file_output, indent=2, ensure_ascii=False)

    print(
        f"  Selesai: {output_data['total']} kalimat, "
        f"kata {output_data['min_words']}-{output_data['max_words']}"
    )

print(
    f"Proses pengelompokan selesai dalam {time.perf_counter() - start_all:.1f} detik."
)
print(f"Hasil tersimpan di folder: {output_dir}")
