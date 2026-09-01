import json
import os

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, './processed2')
output_dir = os.path.join(SCRIPT_DIR, './processed3')


def combine_sentences(sentences: list[str], min_words: int, max_words: int):
    combined = []
    current_group = []
    current_total = 0

    for sentence in sentences:
        words_count = len(sentence.split())
        if current_total + words_count <= max_words:
            current_group.append(sentence)
            current_total += words_count
        else:
            if current_group:
                combined.append(" ".join(current_group))
            current_group = [sentence]
            current_total = words_count

    if current_group:
        combined.append(" ".join(current_group))

    # Filter untuk mengembalikan hanya kalimat yang memenuhi batas minimum kata
    return [
        sentence
        for sentence in combined
        if len(sentence.split()) >= min_words
    ]


def load_file(name):
    path = os.path.join(input_dir, f"{name}.json")
    with open(path, 'r', encoding='utf-8') as file:
        content = json.load(file)
        return [content["total"], content["data"]]


def redistribute(categories: dict[str, list[str]], target: int):
    limits = {
        "pendek": (1, 30),
        "menengah": (31, 60),
        "panjang": (61, 100)
    }

    # Hitung kekurangan dan kelebihan tiap kategori
    difference = {
        key: target - value[0]
        for key, value in categories.items()
    }

    # Pisah kategori ke dalam surplus (kelebihan) dan deficit (kekurangan)
    surplus = {}
    deficit = {}
    for key, value in difference.items():
        if value > 0:
            deficit[key] = value
        elif value < 0:
            surplus[key] = abs(value)

    surplus_pool = []
    for key in list(surplus.keys()):
        # Ambil data surplus dari kategori yang kelebihannya paling panjang terlebih dahulu
        surplus_pool.extend(categories[key][1][target:])

        # Potong kategori surplus tersebut agar hanya menyisakan data hingga target saja
        categories[key][1] = categories[key][1][:target]
        categories[key][0] = len(categories[key][1])

    loop_count = 0
    while True:
        if not surplus_pool:
            break

        pool_len_before = len(surplus_pool)

        # Distribusikan data surplus tersebut ke kategori-kategori yang defisit
        for deficit_category, deficit_count in list(deficit.items()):
            loop_count += 1
            status = ", ".join([f"{k}: {v[0]}" for k, v in categories.items()])
            print(f"Iterasi {loop_count}\n | {status}")

            current_deficit = target - categories[deficit_category][0]
            if current_deficit <= 0 or not surplus_pool:
                continue

            min_words, max_words = limits[deficit_category]
            processed_sentences = []
            used_raw_count = 0

            # Buffer penampung sementara untuk kalimat yang terlalu pendek
            short_buffer = []

            for sentence in surplus_pool:
                if len(processed_sentences) >= current_deficit:
                    break

                words = sentence.split()
                word_len = len(words)
                used_raw_count += 1

                if word_len > max_words:
                    # POTONG: Jika kalimat terlalu panjang, potong sesuai batas maksimum
                    chunk = " ".join(words[:max_words])
                    processed_sentences.append(chunk)

                elif word_len < min_words:
                    # GABUNG: Tumpuk ke dalam buffer
                    short_buffer.append(sentence)

                    # Estimasi kasar: Hitung apakah tumpukan di dalam buffer sudah melebihi min_words
                    buffer_words_len = sum(
                        s.count(' ') + 1 for s in short_buffer)

                    if buffer_words_len >= min_words:
                        combined = combine_sentences(
                            short_buffer, min_words, max_words)
                        if combined:
                            processed_sentences.extend(combined)
                            short_buffer = []  # Kosongkan buffer karena kombinasi sukses
                else:
                    # Pas dengan kriteria min_words dan max_words
                    processed_sentences.append(sentence)

            # Ambil hanya sepanjang yang dibutuhkan untuk memenuhi kekurangan kategori defisit
            final_insert = processed_sentences[:current_deficit]
            categories[deficit_category][1].extend(final_insert)
            categories[deficit_category][0] = len(
                categories[deficit_category][1])

            # update sisa kelebihan
            surplus_pool = surplus_pool[used_raw_count:]

        if len(surplus_pool) == pool_len_before:
            print(
                " | Sisa data di surplus_pool habis disedot/tidak dapat dikombinasikan lagi.")
            break


def save_output(category, data):
    path = os.path.join(output_dir, f"{category}.json")
    word_counts = [len(s.split()) for s in data]
    output_data = {
        "min_words": min(word_counts) if word_counts else 0,
        "max_words": max(word_counts) if word_counts else 0,
        "total": len(data),
        "data": sorted(data)
    }
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False)


def main():
    # Buat folder output jika belum ada
    os.makedirs(output_dir, exist_ok=True)

    data_pendek = load_file("pendek")
    data_menengah = load_file("menengah")
    data_panjang = load_file("panjang")

    categories: dict[str, list[str]] = {
        "pendek": data_pendek,
        "menengah": data_menengah,
        "panjang": data_panjang
    }

    # Menggunakan rasio 20% agar lebih masuk akal berdasarkan total kata vs jumlah kalimat
    total_all = data_pendek[0] + data_menengah[0] + data_panjang[0]
    target = int((total_all // 3) * 0.20)

    redistribute(categories, target)

    for name, data in categories.items():
        save_output(name, data[1])

    print("Selesai. Dataset dibagikan ulang semaksimal mungkin. Hasil di:", output_dir)


if __name__ == "__main__":
    main()
