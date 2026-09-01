import json
import os
import time
from collections import Counter
import math

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, '../../data/00-data/processed')
alphabet = 'abcdefghijklmnopqrstuvwxyz '
date = time.strftime('%Y-%m-%d_%H-%M-%S')


def load_file(name):
    path = os.path.join(input_dir, f"{name}.json")
    with open(path, 'r', encoding='utf-8') as file:
        content = json.load(file)
        return [content["total"], content["data"]]


def save_output(category: str, data: dict, entropy: float, avalanche: float):
    path = os.path.join(
        output_dir, f"{category}.json")

    timedData = [
        {
            "sentence": s,
            "execTime": t * 1e6
        }
        for s, t in zip(data["sentences"], data["encryption_time"])
    ]
    timedData.sort(key=lambda x: x["execTime"])

    output_data = {
        "category": category,
        "total": len(timedData),
        "entropy": entropy,
        "avalanche": avalanche,
        "data": timedData
    }
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)


def save_log(label: str, data: list[str]):
    path = os.path.join(output_dir, f"{label}_{date}_log.json")

    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            try:
                logs = json.load(file)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(data)

    with open(path, 'w', encoding='utf-8') as file:
        json.dump(logs, file, ensure_ascii=False, indent=4)


def encrypt(sentence: str):
    encrypted = ""
    for i, char in enumerate(sentence):
        idx = alphabet.find(char)

        if i % 2 == 0:
            new_idx = (idx + 13) % 27
            encrypted += alphabet[new_idx]
        else:
            new_idx = 26 - (idx + 1) % 27
            encrypted += alphabet[new_idx]
    return encrypted


def decrypt(encrypted: str):
    decrypted = ""
    for i, char in enumerate(encrypted):
        idx = alphabet.find(char)

        if i % 2 == 0:
            new_idx = (idx - 13) % 27
            decrypted += alphabet[new_idx]
        else:
            new_idx = (26 - idx - 1) % 27
            decrypted += alphabet[new_idx]
    return decrypted


def encrypt_sentences(name: str, data: list[str]):
    counter = 0
    step = max(1, data[0] // 100)
    log_buffer = []
    encrypt_sentences = {
        "sentences": [],
        "encryption_time": []
    }

    save_log(
        "encryption_time",
        f"Mulai enkripsi data skalabilitas kategori {name}: {data[0]} kalimat dengan step {step}"
    )

    for sentence in data[1]:
        counter += 1
        start_time = time.perf_counter()

        if counter % step == 0 or counter == data[0]:
            percentage = (counter / data[0]) * 100
            print(
                f"Progress: {percentage:.0f}% ({counter}/{data[0]} kalimat)", end='\r', flush=True)

        encrypted = encrypt(sentence)
        encrypt_sentences["sentences"].append(encrypted)

        decrypted = decrypt(encrypted)

        if decrypted != sentence:
            print(
                f"Enkripsi gagal. Original: {sentence}, Decrypted: {decrypted}")
            save_log(
                "encryption_time",
                f"Error: Enkripsi gagal. Original: {sentence}, Decrypted: {decrypted}"
            )
            break

        end_time = time.perf_counter()
        exec_time = end_time - start_time
        encrypt_sentences["encryption_time"].append(exec_time)

        log_buffer.append(
            f"Kalimat ke-{counter}: {exec_time * 1e6:.2f} mikrodetik")
    print(
        f"Total waktu enkripsi {counter} data: {sum(encrypt_sentences['encryption_time']):.6f} detik")
    save_log("encryption_time", log_buffer)
    save_log(
        "encryption_time",
        f"Total waktu enkripsi: {sum(encrypt_sentences['encryption_time']):.6f} detik"
    )
    return encrypt_sentences


def get_entropy(text):
    counts = Counter(text)
    total_len = len(text)
    return -sum((count/total_len) * math.log2(count / total_len) for count in counts.values())


def validation(ciphertext_all: list[str], plaintext_all: list[str]):
    # Menggabungkan semua kalimat menjadi satu string panjang agar analisis lebih akurat
    full_plaintext = "".join(plaintext_all)
    full_ciphertext = "".join(ciphertext_all)

    entropy_plain = get_entropy(full_plaintext)
    entropy_cipher = get_entropy(full_ciphertext)

    # Avalanche Effect (Mengambil sampel kalimat terakhir untuk konsistensi)
    last_plain = plaintext_all[-1]
    last_cipher = ciphertext_all[-1]

    # Modifikasi 1 karakter di akhir plaintext
    idx = alphabet.find(last_plain[-1])
    new_idx = (idx + 1) % 27
    modified_plain = last_plain[:-1] + alphabet[new_idx]
    modified_cipher = encrypt(modified_plain)

    # Menghitung avalanche berdasarkan perubahan bit
    # Kita bandingkan per karakter dan hitung rasio perubahannya
    diff_count = sum(1 for a, b in zip(last_cipher, modified_cipher) if a != b)
    # Jika panjang string berbeda, kita tambah sisa panjangnya ke hitungan perbedaan
    diff_count += abs(len(last_cipher) - len(modified_cipher))
    avalanche = (diff_count / max(len(last_cipher),
                 len(modified_cipher))) * 100

    return [entropy_plain, entropy_cipher], avalanche


def main():
    data_sedikit = load_file("sedikit")
    data_sedang = load_file("sedang")
    data_banyak = load_file("banyak")

    categories: dict[str, list[str]] = {
        "sedikit": data_sedikit,
        "sedang": data_sedang,
        "banyak": data_banyak
    }

    for name, data in categories.items():
        print(f"Memproses kategori: {name}")
        encrypted_data = encrypt_sentences(name, data)

        entropyValue, avalancheValue = validation(
            encrypted_data["sentences"], data[1])
        print(
            f"Entropy: {entropyValue[0]:.4f} (Plain), {entropyValue[1]:.4f} (Cipher), Avalanche Effect: {avalancheValue:.2f}%")
        save_log(
            "validation",
            f"Kategori {name}: EntropyPlain = {entropyValue[0]:.4f}, EntropyCipher = {entropyValue[1]:.4f}, Avalanche Effect = {avalancheValue:.2f}%"
        )

        save_output(name, encrypted_data, entropyValue, avalancheValue)


if __name__ == "__main__":
    for i in range(1, 4):
        output_dir = os.path.join(
            SCRIPT_DIR, f'./crossOutput/output_{time.strftime("%Y-%m-%d_%H-%M-%S")}')
        os.makedirs(output_dir, exist_ok=True)
        print(f"Iterasi ke-{i}")
        main()
