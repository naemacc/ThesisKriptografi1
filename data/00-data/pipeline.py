import json
import os
import random

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, './cleanedRaw')
output_dir = os.path.join(SCRIPT_DIR, './processed')
os.makedirs(output_dir, exist_ok=True)

LIMITS = {
    "sedikit": 100000,
    "sedang": 500000,
    "banyak": 1000000
}


def get_all_data():
    all_data = []
    for file in os.listdir(input_dir):
        if file.endswith('.json'):
            with open(os.path.join(input_dir, file), 'r', encoding='utf-8') as file_input:
                all_data.extend(json.load(file_input)["data"])
    return list(set(all_data))


def generate_target_data(source_pool: list, target_count: int):
    result = source_pool[:min(len(source_pool), target_count)]
    random.shuffle(source_pool)  # Acak data sumber untuk variasi

    # Augmentasi jika data kurang dari target
    while len(result) < target_count:
        result.append(
            f"{random.choice(source_pool)} {random.choice(source_pool)}")

    return result[:target_count]


# List utama semua data
all_sentences = get_all_data()
print(f"Total data unik ditemukan: {len(all_sentences)}")

for category, limit in LIMITS.items():
    final_data = generate_target_data(all_sentences, limit)

    word_counts = [len(line.split()) for line in final_data]
    output_data = {
        "min_words": min(word_counts) if word_counts else 0,
        "max_words": max(word_counts) if word_counts else 0,
        "total": len(final_data),
        "data": final_data
    }

    with open(os.path.join(output_dir, f"{category}.json"), 'w', encoding='utf-8') as file_output:
        json.dump(output_data, file_output, indent=2, ensure_ascii=False)

print("Proses pengelompokan selesai.")
print(f"Hasil tersimpan di folder: {output_dir}")
