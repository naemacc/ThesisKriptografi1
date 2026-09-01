import json
import os

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, './processed1')
output_dir = os.path.join(SCRIPT_DIR, './processed2')

# Buat folder output jika belum ada
os.makedirs(output_dir, exist_ok=True)

# Kategori pengelompokan berdasarkan jumlah kata menggunakan set() untuk menghindari duplikasi pada list hasil
categories = {
    "pendek": set(),
    "menengah": set(),
    "panjang": set()
}

# Iterasi setiap file JSON di folder input
for file in os.listdir(input_dir):
    if file.endswith('.json'):  # Hanya proses file .JSON
        filepath = os.path.join(input_dir, file)
        try:
            # Baca file JSON
            with open(filepath, 'r', encoding='utf-8') as input_file:
                data = json.load(input_file)
        except Exception as e:
            print(f"Error membaca {file}: {e}")
            continue

        # Iterasi setiap kalimat dalam data
        for sentence in data.get("data", []):
            word_count = len(sentence.split())

            # Tentukan kategori berdasarkan jumlah kata
            if 1 <= word_count <= 30:
                categories["pendek"].add(sentence)
            elif 31 <= word_count <= 60:
                categories["menengah"].add(sentence)
            elif 61 <= word_count <= 100:
                categories["panjang"].add(sentence)

# Simpan hasil pengelompokan ke file terpisah per kategori
for category, lines in categories.items():
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
        "data": sorted_lines
    }

    # Simpan hasil ke file JSON
    output_path = os.path.join(output_dir, f"{category.lower()}.json")
    with open(output_path, 'w', encoding='utf-8') as output_file:
        json.dump(output_data, output_file, indent=2, ensure_ascii=False)

print("Selesai! Hasil pengelompokan disimpan di:", output_dir)
