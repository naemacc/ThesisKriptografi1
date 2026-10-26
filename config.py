from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROCESSED_DIR = ROOT / "data" / "processed"
RUNS_DIR = ROOT / "results" / "runs"

#Jumlah iterasi untuk setiap skenario dan metode
N_ITERATIONS = 3

# Kategori skenario dan metode enkripsi
CATEGORIES = {
    "scale": ["sedikit", "sedang", "banyak"],
    "sense": ["pendek", "menengah", "panjang"],
}
