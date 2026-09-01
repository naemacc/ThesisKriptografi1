import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Variabel global dan konfigurasi
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.max_open_warning': 0})
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
input_dir_scale_group1 = os.path.join(SCRIPT_DIR, '00-Scale', 'crossOutput')
input_dir_scale_group2 = os.path.join(
    SCRIPT_DIR, '00-Scale', 'sequencedOutput')
input_dir_sense_group1 = os.path.join(SCRIPT_DIR, '01-Sense', 'crossOutput')
input_dir_sense_group2 = os.path.join(
    SCRIPT_DIR, '01-Sense', 'sequencedOutput')


def load_data(base_dir, method_name, is_sensitivity=False):
    summary_data = []
    time_data = []

    if is_sensitivity:
        mapping = {'pendek': 'Pendek',
                   'menengah': 'Menengah', 'panjang': 'Panjang'}
    else:
        mapping = {'sedikit': 'Sedikit',
                   'sedang': 'Sedang', 'banyak': 'Banyak'}

    if not os.path.exists(base_dir):
        print(f"[Peringatan] Direktori tidak ditemukan: {base_dir}")
        save_log(
            "hasil", {"Peringatan": f"Direktori tidak ditemukan: {base_dir}"})
        return pd.DataFrame(), pd.DataFrame()

    # Iterasi melalui semua folder output
    for folder in sorted(os.listdir(base_dir)):
        if folder.startswith('output_'):
            iteration_name = folder.replace('output_', '')
            folder_path = os.path.join(base_dir, folder)

            # Iterasi secara dinamis berdasarkan mapping yang aktif
            for cat_key, cat_label in mapping.items():
                file_path = os.path.join(folder_path, f"{cat_key}.json")
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # Hitung rata-rata waktu eksekusi untuk kategori ini
                        mean_time = sum(
                            item['execTime']
                            for item in data['data']
                        ) / len(data['data']) if data['data'] else 0

                        #  Hitung total waktu eksekusi untuk kategori ini
                        total_time = sum(
                            item['execTime']
                            for item in data['data']
                        )

                        # Simpan metrik ringkasan (Entropy & Avalanche)
                        summary_data.append({
                            'Metode': method_name,
                            'Iterasi': iteration_name,
                            'Kategori': cat_label,
                            'Entropy Plain': data['entropy'][0],
                            'Entropy Cipher': data['entropy'][1],
                            'Avalanche (%)': data['avalanche'],
                            'Mean Time (µs)': mean_time,
                            'Total Time (µs)': total_time
                        })

                        # Simpan raw time data untuk T-Test dan Boxplot
                        for item in data['data']:
                            time_data.append({
                                'Metode': method_name,
                                'Kategori': cat_label,
                                'Waktu (µs)': item['execTime']
                            })

    return pd.DataFrame(summary_data), pd.DataFrame(time_data)


def save_log(label: str, data):
    path = os.path.join(SCRIPT_DIR, f"{label}_log.json")

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


def run_analysis(scenario_name, cross_dir, seq_dir, is_sensitivity):
    # Menggunakan Dictionary agar output JSON rapi dan tidak berantakan
    log_dict = {
        "Skenario": scenario_name,
        "T-Test": {},
        "Kenaikan Waktu": {}
    }

    print(f"\nMEMULAI ANALISIS: {scenario_name.upper()}")

    df_summary_cross, df_time_cross = load_data(
        cross_dir, 'Cross', is_sensitivity)
    df_summary_seq, df_time_seq = load_data(
        seq_dir, 'Sequenced', is_sensitivity)

    if df_summary_cross.empty and df_summary_seq.empty:
        print(
            f"Melewati {scenario_name}: Data tidak ditemukan di direktori yang dituju.")
        log_dict["Status"] = "Data tidak ditemukan"
        save_log("hasil", log_dict)
        return

    df_summary = pd.concat(
        [df_summary_cross, df_summary_seq], ignore_index=True)
    df_time = pd.concat([df_time_cross, df_time_seq], ignore_index=True)

    # Menentukan urutan kategori yang benar berdasarkan jenis analisis
    if is_sensitivity:
        cat_order = ['Pendek', 'Menengah', 'Panjang']
    else:
        cat_order = ['Sedikit', 'Sedang', 'Banyak']

    df_summary['Kategori'] = pd.Categorical(
        df_summary['Kategori'], categories=cat_order, ordered=True)
    df_time['Kategori'] = pd.Categorical(
        df_time['Kategori'], categories=cat_order, ordered=True)

    # UJI T-TEST
    print("\nHASIL INDEPENDENT T-TEST (WAKTU EKSEKUSI)")

    for cat in cat_order:
        cross_times = df_time[(df_time['Metode'] == 'Cross') & (
            df_time['Kategori'] == cat)]['Waktu (µs)']
        seq_times = df_time[(df_time['Metode'] == 'Sequenced') & (
            df_time['Kategori'] == cat)]['Waktu (µs)']

        if not cross_times.empty and not seq_times.empty:
            t_stat, p_val = stats.ttest_ind(
                cross_times, seq_times, equal_var=False)  # Welch's t-test
            signifikansi = "Signifikan (H1 diterima)" if p_val < 0.05 else "Tidak Signifikan (H0 diterima)"

            # Print ke terminal
            print(f"Kategori {cat}:")
            print(f"  - n (Cross)           : {cross_times.count()}")
            print(f"  - n (Sequenced)       : {seq_times.count()}")
            print(f"  - Rata-rata Cross     : {cross_times.mean():.4f} µs")
            print(f"  - Rata-rata Sequenced : {seq_times.mean():.4f} µs")
            print(f"  - t-value             : {t_stat:.4f}")
            print(f"  - p-value             : {p_val:.4e} -> {signifikansi}")

            # Simpan ke Log Dictionary
            log_dict["T-Test"][cat] = {
                "n (Cross)": int(cross_times.count()),
                "n (Sequenced)": int(seq_times.count()),
                "Rata-rata Cross (µs)": round(cross_times.mean(), 4),
                "Rata-rata Sequenced (µs)": round(seq_times.mean(), 4),
                "t-value": round(t_stat, 4),
                "p-value": f"{p_val:.4e}",
                "Hasil": signifikansi
            }

    # GRAFIK 1: WAKTU EKSEKUSI (disusun vertikal agar potret)
    fig1, axes1 = plt.subplots(2, 1, figsize=(8.27, 11.69))
    sns.boxplot(data=df_time, x='Kategori', y='Waktu (µs)',
                hue='Metode', showfliers=False, ax=axes1[0])
    axes1[0].set_title(f'Distribusi Waktu Eksekusi ({scenario_name})')

    sns.barplot(data=df_summary, x='Kategori', y='Mean Time (µs)',
                hue='Metode', errorbar='sd', ax=axes1[1])
    axes1[1].set_title(f'Rata-rata Waktu Eksekusi ({scenario_name})')
    plt.tight_layout()
    plt.savefig(f'grafik_1_waktu_{scenario_name.lower()}.png',
                dpi=300, orientation='portrait')

    # ANALISIS SKALABILITAS / SENSITIVITAS
    print("\nANALISIS KENAIKAN WAKTU")

    if is_sensitivity:
        # Pivot tabel untuk menghitung rata-rata antar kategori
        mean_times = df_summary.groupby(['Metode', 'Kategori'], observed=False)[
            'Mean Time (µs)'].mean().unstack()
        y_label1 = 'Mean Time (µs)'
        y_label2 = 'Rata-rata Waktu (µs)'

        for method in ['Cross', 'Sequenced']:
            if method in mean_times.index:
                t_1 = mean_times.loc[method, cat_order[0]]  # Pendek
                t_2 = mean_times.loc[method, cat_order[1]]  # Menengah
                t_3 = mean_times.loc[method, cat_order[2]]  # Panjang

                inc_1 = ((t_2 - t_1) / t_1) * \
                    100 if pd.notna(t_1) and t_1 != 0 else 0
                inc_2 = ((t_3 - t_2) / t_2) * \
                    100 if pd.notna(t_2) and t_2 != 0 else 0

                print(f"Metode {method}:")
                print(
                    f"  - {cat_order[0]} -> {cat_order[1]} : Kenaikan {inc_1:.2f}%")
                print(
                    f"  - {cat_order[1]} -> {cat_order[2]} : Kenaikan {inc_2:.2f}%")

                log_dict["Kenaikan Waktu"][method] = {
                    f"{cat_order[0]} -> {cat_order[1]}": f"{inc_1:.2f}%",
                    f"{cat_order[1]} -> {cat_order[2]}": f"{inc_2:.2f}%"
                }
    else:
        # Pivot tabel untuk menghitung total waktu antar kategori
        # Konversi ke detik: bagi dengan 1.000.000
        df_summary['Total Time (s)'] = df_summary['Total Time (µs)'] / 1e6

        total_times = df_summary.groupby(['Metode', 'Kategori'], observed=False)[
            'Total Time (s)'].sum().unstack()

        y_label1 = 'Total Time (s)'
        y_label2 = 'Total Waktu Eksekusi (detik)'

        # Kalkulasi kenaikan (tetap sama karena persentase tidak terpengaruh satuan)
        for method in ['Cross', 'Sequenced']:
            if method in total_times.index:
                t_1 = total_times.loc[method, cat_order[0]]
                t_2 = total_times.loc[method, cat_order[1]]
                t_3 = total_times.loc[method, cat_order[2]]

                inc_1 = ((t_2 - t_1) / t_1) * 100 if t_1 != 0 else 0
                inc_2 = ((t_3 - t_2) / t_2) * 100 if t_2 != 0 else 0

                print(f"Metode {method} (Total):")
                print(
                    f"  - {cat_order[0]} -> {cat_order[1]} : Kenaikan {inc_1:.2f}%")
                print(
                    f"  - {cat_order[1]} -> {cat_order[2]} : Kenaikan {inc_2:.2f}%")

                log_dict["Kenaikan Waktu"][method] = {
                    f"{cat_order[0]} -> {cat_order[1]}": f"{inc_1:.2f}%",
                    f"{cat_order[1]} -> {cat_order[2]}": f"{inc_2:.2f}%"
                }

    # GRAFIK 2: TREND WAKTU
    plt.figure(figsize=(8.27, 8.27))
    sns.lineplot(data=df_summary, x='Kategori', y=y_label1, hue='Metode',
                 marker='o', linewidth=2.5, errorbar='sd', err_style='bars')
    plt.title(f'Trend Peningkatan Waktu Eksekusi ({scenario_name})')
    plt.ylabel(y_label2)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'grafik_2_trend_{scenario_name.lower()}.png',
                dpi=300, orientation='portrait')

    # GRAFIK 3: ENTROPY & AVALANCHE
    fig3, axes3 = plt.subplots(2, 1, figsize=(8.27, 11.69))

    df_entropy = df_summary.melt(id_vars=['Metode', 'Kategori'], value_vars=[
                                 'Entropy Plain', 'Entropy Cipher'], var_name='Jenis Entropy', value_name='Nilai Entropy')
    # Gabungkan Metode + Jenis Entropy agar Cross Plain/Cipher dan Sequenced
    df_entropy['Grup'] = df_entropy['Metode'] + ' - ' + \
        df_entropy['Jenis Entropy']
    grup_order = ['Cross - Entropy Plain', 'Cross - Entropy Cipher',
                  'Sequenced - Entropy Plain', 'Sequenced - Entropy Cipher']
    grup_order = [g for g in grup_order if g in df_entropy['Grup'].unique()]
    sns.barplot(data=df_entropy, x='Kategori', y='Nilai Entropy',
                hue='Grup', hue_order=grup_order, errorbar=None, ax=axes3[0])
    axes3[0].set_title(f'Entropy Plaintext vs Ciphertext ({scenario_name})')
    axes3[0].set_ylim(0, 5)
    axes3[0].legend(title='Skema - Jenis', fontsize=8)

    sns.barplot(data=df_summary, x='Kategori', y='Avalanche (%)',
                hue='Metode', errorbar='sd', ax=axes3[1])
    axes3[1].set_title(f'Perbandingan Avalanche Effect ({scenario_name})')

    plt.tight_layout()
    plt.savefig(f'grafik_3_keamanan_{scenario_name.lower()}.png',
                dpi=300, orientation='portrait')

    print(
        f"[Sukses] Grafik untuk {scenario_name} telah disimpan ke direktori saat ini.")

    # Simpan Dictionary terstruktur ke JSON
    save_log("hasil", log_dict)


def main():
    # Skalabilitas (Scale)
    run_analysis(
        scenario_name="Skalabilitas",
        cross_dir=input_dir_scale_group1,
        seq_dir=input_dir_scale_group2,
        is_sensitivity=False
    )

    # Sensitivitas (Sense)
    run_analysis(
        scenario_name="Sensitivitas",
        cross_dir=input_dir_sense_group1,
        seq_dir=input_dir_sense_group2,
        is_sensitivity=True
    )

    plt.show()


if __name__ == "__main__":
    main()
