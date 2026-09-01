import json
import os
import string

# Folder input/output
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir = os.path.join(SCRIPT_DIR, './raw')
output_dir = os.path.join(SCRIPT_DIR, './processed1')

# Buat folder output jika belum ada
os.makedirs(output_dir, exist_ok=True)


def clean_az(text):  # Fungsi pembersih teks

    # Ubah ke huruf kecil dan bentuk filter karakter
    lower_text = text.lower()
    allowed = string.ascii_lowercase + " "  # String a-z dan spasi
    result_text = []

    # Filter karakter menjadi huruf dan tidak kapital (a-z dan spasi saja).
    for char in lower_text:
        if char in allowed:
            result_text.append(char)

    # Gabungkan list of chars menjadi string lagi
    cleaned_text = "".join(result_text)

    # Buang spasi berlebih di depan/belakang
    return cleaned_text.strip()


for file in os.listdir(input_dir):  # Iterasi semua file di folder
    if file.endswith('.json'):  # Cek file .JSON saja
        filepath = os.path.join(input_dir, file)
        try:
            # Baca file JSON
            with open(filepath, 'r') as input_file:
                data = json.load(input_file)
        except Exception as e:
            print(f"Error membaca {file}: {e}")
            continue

        cleaned_sentences = []
        conversation = data.get("conversations", [])[0]

        # Ambil string kalimat berdasarkan bentuk dataset
        for line in conversation:
            sentence = line[0]
            cleaned = clean_az(sentence)
            # Hanya simpan kalimat yang tidak kosong
            if cleaned:
                cleaned_sentences.append(cleaned)

        # Buat data output dalam format JSON
        output_data = {
            "data": cleaned_sentences
        }

        # Tulis hasil ke file baru di folder output
        output_path = os.path.join(output_dir, file)
        with open(output_path, 'w') as output_file:
            json.dump(output_data, output_file, indent=2)

print("Selesai! Hasil penyesuaian disimpan di:", output_dir)
