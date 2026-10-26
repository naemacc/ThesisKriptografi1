import os
import sys
import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# result.py berada di folder analysis, jadi folder induk ditambahkan ke sys.path
# agar config dapat diimpor
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import RUNS_DIR

# Variabel global dan konfigurasi
sns.set_theme(style="whitegrid")
plt.rcParams.update({"figure.max_open_warning": 0})

# Hasil analisis (grafik dan log) disimpan di results/, terpisah dari kode
RESULTS_DIR = RUNS_DIR.parent
FIGURES_DIR = RESULTS_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Folder input: results/runs/<skenario>/<metode>/
input_dir_scale_group1 = RUNS_DIR / "scale" / "cross"
input_dir_scale_group2 = RUNS_DIR / "scale" / "sequenced"
input_dir_sense_group1 = RUNS_DIR / "sense" / "cross"
input_dir_sense_group2 = RUNS_DIR / "sense" / "sequenced"


def simpan_grafik(nama):
    plt.savefig(FIGURES_DIR / nama, dpi=300)


def save_log(label: str, data):
    path = os.path.join(RESULTS_DIR, f"{label}_log.json")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            try:
                logs = json.load(file)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append(data)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(logs, file, ensure_ascii=False, indent=4)


def load_data(base_dir, method_name, is_sensitivity=False):
    summary_data = []
    time_data = []

    if is_sensitivity:
        mapping = {"pendek": "Pendek", "menengah": "Menengah", "panjang": "Panjang"}
    else:
        mapping = {"sedikit": "Sedikit", "sedang": "Sedang", "banyak": "Banyak"}

    if not os.path.exists(base_dir):
        print(f"[Peringatan] Direktori tidak ditemukan: {base_dir}")
        save_log("hasil", {"Peringatan": f"Direktori tidak ditemukan: {base_dir}"})
        return pd.DataFrame(), pd.DataFrame()

    # Iterasi melalui semua folder run (nama folder berupa timestamp)
    for folder in sorted(os.listdir(base_dir)):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        # replace tetap dipertahankan agar folder lama (output_...) masih terbaca
        iteration_name = folder.replace("output_", "")

        # Iterasi berdasarkan mapping kategori yang aktif
        for cat_key, cat_label in mapping.items():
            file_path = os.path.join(folder_path, f"{cat_key}.json")
            if not os.path.exists(file_path):
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            exec_times = [item["execTime"] for item in data["data"]]
            total_time = sum(exec_times)
            mean_time = total_time / len(exec_times) if exec_times else 0

            # Simpan metrik ringkasan (Entropy, Avalanche, Waktu)
            summary_data.append(
                {
                    "Metode": method_name,
                    "Iterasi": iteration_name,
                    "Kategori": cat_label,
                    "Entropy Plain": data["entropy"][0],
                    "Entropy Cipher": data["entropy"][1],
                    "Avalanche (%)": data["avalanche"],
                    "Mean Time (µs)": mean_time,
                    "Total Time (µs)": total_time,
                }
            )

            # Simpan data waktu mentah untuk T-Test dan Boxplot
            for t in exec_times:
                time_data.append(
                    {"Metode": method_name, "Kategori": cat_label, "Waktu (µs)": t}
                )

    return pd.DataFrame(summary_data), pd.DataFrame(time_data)


def hitung_kenaikan(tabel, cat_order, judul, log_dict):
    # Hitung persentase kenaikan waktu antar kategori berurutan untuk tiap metode
    for method in ["Cross", "Sequenced"]:
        if method not in tabel.index:
            continue

        t_1, t_2, t_3 = (tabel.loc[method, c] for c in cat_order)

        inc_1 = ((t_2 - t_1) / t_1) * 100 if pd.notna(t_1) and t_1 != 0 else 0
        inc_2 = ((t_3 - t_2) / t_2) * 100 if pd.notna(t_2) and t_2 != 0 else 0

        print(f"Metode {method}{judul}:")
        print(f"  - {cat_order[0]} -> {cat_order[1]} : Kenaikan {inc_1:.2f}%")
        print(f"  - {cat_order[1]} -> {cat_order[2]} : Kenaikan {inc_2:.2f}%")

        log_dict["Kenaikan Waktu"][method] = {
            f"{cat_order[0]} -> {cat_order[1]}": f"{inc_1:.2f}%",
            f"{cat_order[1]} -> {cat_order[2]}": f"{inc_2:.2f}%",
        }


def buat_data_entropy(df_summary, log_dict):
    # Plaintext identik untuk kedua metode, jadi cukup ditampilkan 1 bar per kategori.
    # Nilai plaintext diambil per (Iterasi, Kategori) lalu dicek konsistensinya.
    plain = (
        df_summary.groupby(["Iterasi", "Kategori"], observed=True)
        .agg(
            nilai=("Entropy Plain", "mean"),
            selisih=("Entropy Plain", lambda s: s.max() - s.min()),
        )
        .reset_index()
    )

    if plain["selisih"].max() > 1e-6:
        pesan = "Entropy plaintext berbeda antar metode, periksa data input."
        print(f"[Peringatan] {pesan}")
        log_dict["Peringatan Entropy"] = pesan

    df_plain = pd.DataFrame(
        {
            "Kategori": plain["Kategori"],
            "Nilai Entropy": plain["nilai"],
            "Grup": "Plaintext",
        }
    )

    # Ciphertext tetap dipisah per metode karena nilainya memang berbeda
    df_cipher = pd.DataFrame(
        {
            "Kategori": df_summary["Kategori"],
            "Nilai Entropy": df_summary["Entropy Cipher"],
            "Grup": df_summary["Metode"] + " (Cipher)",
        }
    )

    df_entropy = pd.concat([df_plain, df_cipher], ignore_index=True)
    grup_order = [
        g
        for g in ["Plaintext", "Cross (Cipher)", "Sequenced (Cipher)"]
        if g in df_entropy["Grup"].unique()
    ]
    return df_entropy, grup_order


def run_analysis(scenario_name, cross_dir, seq_dir, is_sensitivity):
    # Menggunakan Dictionary agar output JSON rapi
    log_dict = {"Skenario": scenario_name, "T-Test": {}, "Kenaikan Waktu": {}}

    print(f"\nMEMULAI ANALISIS: {scenario_name.upper()}")

    df_summary_cross, df_time_cross = load_data(cross_dir, "Cross", is_sensitivity)
    df_summary_seq, df_time_seq = load_data(seq_dir, "Sequenced", is_sensitivity)

    if df_summary_cross.empty and df_summary_seq.empty:
        print(
            f"Melewati {scenario_name}: Data tidak ditemukan di direktori yang dituju."
        )
        log_dict["Status"] = "Data tidak ditemukan"
        save_log("hasil", log_dict)
        return

    df_summary = pd.concat([df_summary_cross, df_summary_seq], ignore_index=True)
    df_time = pd.concat([df_time_cross, df_time_seq], ignore_index=True)

    # Urutan kategori sesuai jenis analisis
    if is_sensitivity:
        cat_order = ["Pendek", "Menengah", "Panjang"]
    else:
        cat_order = ["Sedikit", "Sedang", "Banyak"]

    df_summary["Kategori"] = pd.Categorical(
        df_summary["Kategori"], categories=cat_order, ordered=True
    )
    df_time["Kategori"] = pd.Categorical(
        df_time["Kategori"], categories=cat_order, ordered=True
    )

    # UJI T-TEST (Welch) pada data waktu mentah per item
    print("\nHASIL INDEPENDENT T-TEST (WAKTU EKSEKUSI)")

    for cat in cat_order:
        cross_times = df_time[
            (df_time["Metode"] == "Cross") & (df_time["Kategori"] == cat)
        ]["Waktu (µs)"]
        seq_times = df_time[
            (df_time["Metode"] == "Sequenced") & (df_time["Kategori"] == cat)
        ]["Waktu (µs)"]

        if not cross_times.empty and not seq_times.empty:
            t_stat, p_val = stats.ttest_ind(cross_times, seq_times, equal_var=False)
            signifikansi = (
                "Signifikan (H1 diterima)"
                if p_val < 0.05
                else "Tidak Signifikan (H0 diterima)"
            )

            print(f"Kategori {cat}:")
            print(f"  - n (Cross)           : {cross_times.count()}")
            print(f"  - n (Sequenced)       : {seq_times.count()}")
            print(f"  - Rata-rata Cross     : {cross_times.mean():.4f} µs")
            print(f"  - Rata-rata Sequenced : {seq_times.mean():.4f} µs")
            print(f"  - t-value             : {t_stat:.4f}")
            print(f"  - p-value             : {p_val:.4e} -> {signifikansi}")

            log_dict["T-Test"][cat] = {
                "n (Cross)": int(cross_times.count()),
                "n (Sequenced)": int(seq_times.count()),
                "Rata-rata Cross (µs)": round(cross_times.mean(), 4),
                "Rata-rata Sequenced (µs)": round(seq_times.mean(), 4),
                "t-value": round(t_stat, 4),
                "p-value": f"{p_val:.4e}",
                "Hasil": signifikansi,
            }

    # GRAFIK 1: DISTRIBUSI WAKTU EKSEKUSI
    # Boxplot menampilkan sebaran data mentah yang dipakai T-Test (median, spread, overlap).
    # Marker berlian = rata-rata, agar konsisten dengan nilai rata-rata pada T-Test.
    # Barplot rata-rata dihapus karena sudah terwakili marker rata-rata dan Grafik 2.
    plt.figure(figsize=(8.27, 6))
    sns.boxplot(
        data=df_time,
        x="Kategori",
        y="Waktu (µs)",
        hue="Metode",
        showfliers=False,
        showmeans=True,
        meanprops={
            "marker": "D",
            "markerfacecolor": "white",
            "markeredgecolor": "black",
            "markersize": 6,
        },
    )
    plt.title(f"Distribusi Waktu Eksekusi ({scenario_name})")
    plt.tight_layout()
    simpan_grafik(f"grafik_1_waktu_{scenario_name.lower()}.png")

    # ANALISIS KENAIKAN WAKTU
    print("\nANALISIS KENAIKAN WAKTU")

    if is_sensitivity:
        # Sensitivitas: bandingkan rata-rata waktu per item antar kategori
        tabel = (
            df_summary.groupby(["Metode", "Kategori"], observed=False)["Mean Time (µs)"]
            .mean()
            .unstack()
        )
        y_label1 = "Mean Time (µs)"
        y_label2 = "Rata-rata Waktu (µs)"
        hitung_kenaikan(tabel, cat_order, "", log_dict)
    else:
        # Skalabilitas: bandingkan total waktu (detik) antar kategori
        df_summary["Total Time (s)"] = df_summary["Total Time (µs)"] / 1e6
        tabel = (
            df_summary.groupby(["Metode", "Kategori"], observed=False)["Total Time (s)"]
            .sum()
            .unstack()
        )
        y_label1 = "Total Time (s)"
        y_label2 = "Total Waktu Eksekusi (detik)"
        hitung_kenaikan(tabel, cat_order, " (Total)", log_dict)

    # GRAFIK 2: TREND WAKTU
    plt.figure(figsize=(8.27, 8.27))
    sns.lineplot(
        data=df_summary,
        x="Kategori",
        y=y_label1,
        hue="Metode",
        marker="o",
        linewidth=2.5,
        errorbar="sd",
        err_style="bars",
    )
    plt.title(f"Trend Peningkatan Waktu Eksekusi ({scenario_name})")
    plt.ylabel(y_label2)
    plt.tight_layout()
    simpan_grafik(f"grafik_2_trend_{scenario_name.lower()}.png")

    # GRAFIK 3: ENTROPY
    # 3 bar per kategori (Plaintext, Cross Cipher, Sequenced Cipher)
    plt.figure(figsize=(8.27, 6))
    df_entropy, grup_order = buat_data_entropy(df_summary, log_dict)
    sns.barplot(
        data=df_entropy,
        x="Kategori",
        y="Nilai Entropy",
        hue="Grup",
        hue_order=grup_order,
        errorbar="sd",
    )
    plt.title(f"Entropy Plaintext vs Ciphertext ({scenario_name})")
    plt.legend(title="Data", fontsize=8)
    plt.tight_layout()
    simpan_grafik(f"grafik_3_entropy_{scenario_name.lower()}.png")

    # GRAFIK 4: AVALANCHE
    # Garis 50% adalah nilai ideal sebagai acuan
    plt.figure(figsize=(8.27, 6))
    sns.barplot(
        data=df_summary,
        x="Kategori",
        y="Avalanche (%)",
        hue="Metode",
        errorbar="sd",
    )
    plt.axhline(50, color="red", linestyle="--", linewidth=1, label="Ideal (50%)")
    plt.title(f"Perbandingan Avalanche Effect ({scenario_name})")
    plt.legend(fontsize=8)
    plt.tight_layout()
    simpan_grafik(f"grafik_4_avalanche_{scenario_name.lower()}.png")

    print(f"[Sukses] Grafik untuk {scenario_name} disimpan di: {FIGURES_DIR}")

    # Simpan Dictionary terstruktur ke JSON
    save_log("hasil", log_dict)


def main():
    # Skalabilitas (Scale)
    run_analysis(
        scenario_name="Skalabilitas",
        cross_dir=input_dir_scale_group1,
        seq_dir=input_dir_scale_group2,
        is_sensitivity=False,
    )

    # Sensitivitas (Sense)
    run_analysis(
        scenario_name="Sensitivitas",
        cross_dir=input_dir_sense_group1,
        seq_dir=input_dir_sense_group2,
        is_sensitivity=True,
    )

    plt.show()


if __name__ == "__main__":
    main()
