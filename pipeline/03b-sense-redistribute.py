import json
import os
import time

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, "../data/interim/sense-categorized")
output_dir = os.path.join(SCRIPT_DIR, "../data/processed/sense")


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
    return [sentence for sentence in combined if len(sentence.split()) >= min_words]


def load_file(name):
    path = os.path.join(input_dir, f"{name}.json")
    print(f"Membaca {name}.json ...")
    with open(path, "r", encoding="utf-8") as file:
        content = json.load(file)
        return [content["total"], content["data"]]


def redistribute(categories: dict[str, list[str]], target: int):
    limits = {"pendek": (1, 30), "menengah": (31, 60), "panjang": (61, 100)}

    # Hitung kekurangan dan kelebihan tiap kategori
    difference = {key: target - value[0] for key, value in categories.items()}

    # Pisah kategori ke dalam surplus (kelebihan) dan deficit (kekurangan)
    surplus = {}
    deficit = {}
    for key, value in difference.items():
        if value > 0:
            deficit[key] = value
        elif value < 0:
            surplus[key] = abs(value)

    print(f"Target per kategori : {target}")
    print(f"Surplus             : {surplus}")
    print(f"Defisit             : {deficit}")

    surplus_pool = []
    for key in list(surplus.keys()):
        # Ambil data surplus dari kategori yang kelebihannya paling panjang terlebih dahulu
        surplus_pool.extend(categories[key][1][target:])

        # Potong kategori surplus tersebut agar hanya menyisakan data hingga target saja
        categories[key][1] = categories[key][1][:target]
        categories[key][0] = len(categories[key][1])

    print(f"Ukuran surplus_pool : {len(surplus_pool)}")

    loop_count = 0
    while True:
        if not surplus_pool:
            break

        pool_len_before = len(surplus_pool)

        # Distribusikan data surplus tersebut ke kategori-kategori yang defisit
        for deficit_category, deficit_count in list(deficit.items()):
            loop_count += 1
            status = ", ".join([f"{k}: {v[0]}" for k, v in categories.items()])
            print(f"Iterasi {loop_count} ({deficit_category})")
            print(f" | {status} | sisa pool: {len(surplus_pool)}")

            current_deficit = target - categories[deficit_category][0]
            if current_deficit <= 0 or not surplus_pool:
                print(" | Dilewati (sudah terpenuhi / pool kosong)")
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

                # Cetak status setiap 1000 kalimat sumber yang diperiksa
                if used_raw_count % 1000 == 0:
                    print(
                        f" | Diperiksa {used_raw_count} kalimat, "
                        f"terkumpul {len(processed_sentences)}/{current_deficit}",
                        end="\r",
                        flush=True,
                    )

                if word_len > max_words:
                    # POTONG: Jika kalimat terlalu panjang, potong sesuai batas maksimum
                    chunk = " ".join(words[:max_words])
                    processed_sentences.append(chunk)

                elif word_len < min_words:
                    # GABUNG: Tumpuk ke dalam buffer
                    short_buffer.append(sentence)

                    # Estimasi kasar: Hitung apakah tumpukan di dalam buffer sudah melebihi min_words
                    buffer_words_len = sum(s.count(" ") + 1 for s in short_buffer)

                    if buffer_words_len >= min_words:
                        combined = combine_sentences(short_buffer, min_words, max_words)
                        if combined:
                            processed_sentences.extend(combined)
                            short_buffer = (
                                []
                            )  # Kosongkan buffer karena kombinasi sukses
                else:
                    # Pas dengan kriteria min_words dan max_words
                    processed_sentences.append(sentence)

            # Ambil hanya sepanjang yang dibutuhkan untuk memenuhi kekurangan kategori defisit
            final_insert = processed_sentences[:current_deficit]
            categories[deficit_category][1].extend(final_insert)
            categories[deficit_category][0] = len(categories[deficit_category][1])

            print(
                f" | Selesai: +{len(final_insert)} kalimat dari "
                f"{used_raw_count} sumber" + " " * 20
            )

            # update sisa kelebihan
            surplus_pool = surplus_pool[used_raw_count:]

        if len(surplus_pool) == pool_len_before:
            print(
                " | Sisa data di surplus_pool habis disedot/tidak dapat dikombinasikan lagi."
            )
            break


def save_output(category, data):
    path = os.path.join(output_dir, f"{category}.json")
    print(f"  Menyimpan '{category}' ({len(data)} kalimat) ...")
    word_counts = [len(s.split()) for s in data]
    output_data = {
        "min_words": min(word_counts) if word_counts else 0,
        "max_words": max(word_counts) if word_counts else 0,
        "total": len(data),
        "data": sorted(data),
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(output_data, file, ensure_ascii=False)


def main():
    start_all = time.perf_counter()

    # Buat folder output jika belum ada
    os.makedirs(output_dir, exist_ok=True)

    data_pendek = load_file("pendek")
    data_menengah = load_file("menengah")
    data_panjang = load_file("panjang")

    categories: dict[str, list[str]] = {
        "pendek": data_pendek,
        "menengah": data_menengah,
        "panjang": data_panjang,
    }

    print(
        "Jumlah awal -> "
        + ", ".join(f"{k}: {v[0]}" for k, v in categories.items())
    )

    # Menggunakan rasio 20% agar lebih masuk akal berdasarkan total kata vs jumlah kalimat
    total_all = data_pendek[0] + data_menengah[0] + data_panjang[0]
    target = int((total_all // 3) * 0.20)

    redistribute(categories, target)

    print("Jumlah akhir -> " + ", ".join(f"{k}: {v[0]}" for k, v in categories.items()))
    print("Menyimpan hasil ...")
    for name, data in categories.items():
        save_output(name, data[1])

    print(f"Selesai dalam {time.perf_counter() - start_all:.1f} detik.")
    print("Dataset dibagikan ulang semaksimal mungkin. Hasil di:", output_dir)


if __name__ == "__main__":
    main()