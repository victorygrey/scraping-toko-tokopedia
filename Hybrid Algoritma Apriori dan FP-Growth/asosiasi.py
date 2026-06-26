import pandas as pd
from itertools import combinations
import glob
import time
from datetime import datetime

# ======================================================
# 1. Load frequent itemsets hybrid
# ======================================================
proses1_start = time.time()

print("\n" + "="*70)
print("STEP 1: LOAD FREQUENT ITEMSETS HYBRID")
print("="*70)
print("Proses: Membaca file frequent_itemsets_hybrid terbaru dari direktori...")
print("Deskripsi: Mencari file frequent_itemsets_hybrid_*.csv yang paling baru,")
print("           memuat data frequent itemsets dari proses hybrid mining,")
print("           dan mengkonversi format itemsets dari string ke tuple.")
print("-"*70)

# Cari file frequent_itemsets_hybrid terbaru
freq_files = glob.glob("frequent_itemsets_hybrid*.csv")
if not freq_files:
    print("Error: Tidak ada file frequent_itemsets_hybrid ditemukan!")
    exit()

latest_freq_file = max(freq_files)
print(f"File terbaru ditemukan: {latest_freq_file}")

df = pd.read_csv(latest_freq_file)
print(f"Total itemsets dimuat: {len(df)} baris")
print(f"Kolom ditemukan: {df.columns.tolist()}")

# gunakan kolom itemsets (berdasarkan CSV kamu)
itemset_col = "itemsets"

# pastikan kolom itemsets berubah dari string -> list
def parse_itemset(x):
    val = eval(x) if isinstance(x, str) else x
    # Jika tuple satu elemen, ubah ke list
    if isinstance(val, tuple):
        val = list(val)
    return val

df[itemset_col] = df[itemset_col].apply(parse_itemset)

print(f"\nHasil konversi itemsets:")
print(f"  - Type itemsets setelah konversi: {type(df[itemset_col].iloc[0])}")
print(f"  - Contoh itemsets pertama: {df[itemset_col].iloc[0]}")
print(f"  - Support itemset pertama: {df['support'].iloc[0]:.4f}")
print(f"  - Range support: {df['support'].min():.4f} - {df['support'].max():.4f}")

# buat dict: tuple(itemset) -> support
support_dict = {
    tuple(sorted(items)): support
    for items, support in zip(df[itemset_col], df["support"])
}

print(f"\nSupport Dictionary:")
print(f"  - Total itemsets dalam dict: {len(support_dict)}")
print(f"  - Contoh (pertama 3 itemsets):")
for i, (itemset, sup) in enumerate(list(support_dict.items())[:3]):
    print(f"    {i+1}. {itemset} -> support: {sup:.4f}")

proses1_end = time.time()
duration1 = proses1_end - proses1_start

# Format output durasi
if duration1 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration1:.2f} detik")
else:
    duration1_ms = duration1 * 1000
    print(f"⏱️  Waktu eksekusi: {duration1_ms:.2f} milidetik")

# Konfirmasi
while True:
    confirm = input("\n✓ Apakah ingin dilanjut? (Y/N): ").upper().strip()
    if confirm == 'Y':
        break
    elif confirm == 'N':
        print("Program dibatalkan.")
        exit()
    else:
        print("Input tidak valid. Masukkan Y atau N.")


# ======================================================
# 2. Generate Association Rules
# ======================================================
proses2_start = time.time()

print("\n" + "="*70)
print("STEP 2: GENERATE ASSOCIATION RULES")
print("="*70)
print("Proses: Menghasilkan association rules dari frequent itemsets...")
print("Deskripsi: Association rules adalah aturan yang menunjukkan hubungan")
print("           antara itemsets dalam bentuk: antecedent -> consequent")
print("           dengan metrik: confidence, lift, dan support.")
print("-"*70)

rules = []
total_itemsets_checked = 0
total_combinations_checked = 0

print(f"\nProses pengecekan itemsets:")
print(f"  - Hanya itemsets dengan 2+ items yang akan diproses...")

for itemset, support_itemset in support_dict.items():
    if len(itemset) < 2:
        continue
    
    total_itemsets_checked += 1

    for i in range(1, len(itemset)):
        for antecedent in combinations(itemset, i):
            total_combinations_checked += 1
            antecedent = tuple(sorted(antecedent))
            consequent = tuple(sorted(set(itemset) - set(antecedent)))

            support_antecedent = support_dict.get(antecedent)
            support_consequent = support_dict.get(consequent)

            if support_antecedent is None or support_consequent is None:
                continue

            confidence = support_itemset / support_antecedent
            lift = confidence / support_consequent

            rules.append({
                "antecedent": antecedent,
                "consequent": consequent,
                "support": support_itemset,
                "confidence": confidence,
                "lift": lift
            })

print(f"\nHasil scanning:")
print(f"  - Total itemsets dengan 2+ items: {total_itemsets_checked}")
print(f"  - Total kombinasi yang dicek: {total_combinations_checked}")
print(f"  - Total rules yang dihasilkan: {len(rules)}")

# Analisis rules berdasarkan confidence dan lift
if rules:
    rules_df_temp = pd.DataFrame(rules)
    print(f"\nStatistik Association Rules:")
    print(f"  - Support:")
    print(f"    * Min: {rules_df_temp['support'].min():.4f}")
    print(f"    * Max: {rules_df_temp['support'].max():.4f}")
    print(f"    * Mean: {rules_df_temp['support'].mean():.4f}")
    print(f"  - Confidence:")
    print(f"    * Min: {rules_df_temp['confidence'].min():.4f}")
    print(f"    * Max: {rules_df_temp['confidence'].max():.4f}")
    print(f"    * Mean: {rules_df_temp['confidence'].mean():.4f}")
    print(f"  - Lift:")
    print(f"    * Min: {rules_df_temp['lift'].min():.4f}")
    print(f"    * Max: {rules_df_temp['lift'].max():.4f}")
    print(f"    * Mean: {rules_df_temp['lift'].mean():.4f}")
    
    print(f"\nContoh Association Rules (top 5):")
    top_rules = rules_df_temp.nlargest(5, 'lift')
    for idx, row in top_rules.iterrows():
        print(f"  {idx+1}. {row['antecedent']} => {row['consequent']}")
        print(f"     Support: {row['support']:.4f} | Confidence: {row['confidence']:.4f} | Lift: {row['lift']:.4f}")
else:
    print("  ⚠ Tidak ada association rules yang dihasilkan!")

proses2_end = time.time()
duration2 = proses2_end - proses2_start

# Format output durasi
if duration2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration2:.2f} detik")
else:
    duration2_ms = duration2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration2_ms:.2f} milidetik")

# Konfirmasi
while True:
    confirm = input("\n✓ Apakah ingin dilanjut? (Y/N): ").upper().strip()
    if confirm == 'Y':
        break
    elif confirm == 'N':
        print("Program dibatalkan.")
        exit()
    else:
        print("Input tidak valid. Masukkan Y atau N.")


# ======================================================
# 3. Save to CSV
# ======================================================
print("\n" + "="*70)
print("STEP 3: SAVE ASSOCIATION RULES TO CSV")
print("="*70)
print("Proses: Menyimpan hasil association rules ke file CSV...")
print("Deskripsi: Semua association rules akan disimpan dalam format CSV")
print("           untuk analisis dan penggunaan lebih lanjut.")
print("-"*70)

rules_df = pd.DataFrame(rules)
# Pastikan antecedent dan consequent berupa list dan format string list
if not rules_df.empty:
    rules_df['antecedent'] = rules_df['antecedent'].apply(lambda x: list(x) if not isinstance(x, list) else x)
    rules_df['antecedent'] = rules_df['antecedent'].apply(lambda x: repr(x))
    rules_df['consequent'] = rules_df['consequent'].apply(lambda x: list(x) if not isinstance(x, list) else x)
    rules_df['consequent'] = rules_df['consequent'].apply(lambda x: repr(x))

output_filename = f"association_rules_hybrid_{datetime.now().strftime('%d%b%Y')}.csv"
rules_df.to_csv(output_filename, index=False)

print(f"\n✓ File berhasil disimpan!")
print(f"  - Filename: {output_filename}")
print(f"  - Total baris: {len(rules_df)}")
print(f"  - Kolom: {rules_df.columns.tolist()}")

print(f"\nSample output (5 baris pertama):")
print(rules_df.head(5).to_string(index=False))

print("\n" + "="*70)
print("Program selesai! ✓")

totalduration = duration1 + duration2
if totalduration >= 1:
    print(f"⏱️  Total waktu eksekusi: {totalduration:.2f} detik")
else:
    totalduration_ms = totalduration * 1000
    print(f"⏱️  Total waktu eksekusi: {totalduration_ms:.2f} milidetik")

print("="*70)
