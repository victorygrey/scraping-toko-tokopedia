import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
import pyfpgrowth
import glob
import time
from datetime import datetime

# ========================================
# LOAD TRANSAKSI
# ========================================
proses1_start = time.time()

print("\n" + "="*60)
print("STEP 0: LOAD TRANSAKSI")
print("="*60)
print("Proses: Membaca file transaksi terbaru dari direktori...")
print("Deskripsi: Mencari file transactions_*.csv yang paling baru,")
print("           memuat data, dan mengubah format nama produk menjadi list.")
print("-"*60)

files = glob.glob("transactions_raw_*.csv")
if not files:
    print("Error: Tidak ada file transactions_*.csv ditemukan!")
    exit()

def get_file_date(filename):
    """Extract dan parse tanggal dari nama file"""
    try:
        date_part = filename.split('_')[-1].replace('.csv', '')
        # Coba berbagai format tanggal
        for fmt in ['%d%b%y', '%Y%m%d', '%d-%m-%Y']:
            try:
                return datetime.strptime(date_part, fmt)
            except ValueError:
                continue
        # Jika semua format gagal, return None (file akan di-filter)
        return None
    except:
        return None

# Filter files dengan tanggal yang valid, jika tidak ada gunakan file terakhir
valid_files = {f: get_file_date(f) for f in files}
valid_files = {f: d for f, d in valid_files.items() if d is not None}

if valid_files:
    latest_file = max(valid_files, key=valid_files.get)
else:
    latest_file = max(files)

print(f"File terbaru ditemukan: {latest_file}")
df = pd.read_csv(latest_file)
print(f"Total transaksi dalam file: {len(df)} baris")
print(f"Kolom yang tersedia: {df.columns.tolist()}")

transactions = df["productName"].apply(lambda x: x.strip("[]").split(","))
transactions = [[i.strip().strip("'").strip('"') for i in row] for row in transactions]

print(f"\nHasil transformasi:")
print(f"  - Total transaksi: {len(transactions)}")
print(f"  - Contoh transaksi pertama: {transactions[0][:3]}{'...' if len(transactions[0]) > 3 else ''}")
print(f"  - Unique items: {len(set(i for trx in transactions for i in trx))}")

end1_time = time.time()
duration1 = end1_time - proses1_start

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


# ========================================
# STEP 1: APRIORI TAHAP AWAL (F1 & F2)
# ========================================
proses2_start = time.time()

print("\n" + "="*60)
print("STEP 1: APRIORI TAHAP AWAL (F1 & F2)")
print("="*60)
print("Proses: Mencari frequent itemsets menggunakan algoritma Apriori")
print("        untuk 1-itemset (F1) dan 2-itemset (F2).")
print("Deskripsi: Apriori adalah algoritma data mining yang mencari")
print("           kombinasi produk yang sering muncul bersama dalam transaksi.")
print("           Min support threshold: 0.01 (1% dari total transaksi)")
print("-"*60)

te = TransactionEncoder()
te_data = te.fit(transactions).transform(transactions)
df_ap = pd.DataFrame(te_data, columns=te.columns_)

print(f"Data matrix Apriori:")
print(f"  - Ukuran matrix: {df_ap.shape[0]} transaksi x {df_ap.shape[1]} items")
print(f"  - Total items unik: {len(te.columns_)}")

# Ambil frequent itemset hanya sampai 2 item
F1 = apriori(df_ap, min_support=0.01, use_colnames=True)
F2 = apriori(df_ap, min_support=0.01, use_colnames=True, max_len=2)

print(f"\nHasil Apriori:")
print(f"  - F1 (1-itemset): {len(F1)} itemset")
print(f"  - F2 (2-itemset): {len(F2)} itemset")
print(f"\nContoh F1 (top 3):")
print(F1.head(3).to_string(index=False))
print(f"\nContoh F2 (top 3):")
print(F2.head(3).to_string(index=False))

apriori_itemsets = pd.concat([F1, F2])
print(f"\nTotal itemsets Apriori (F1 + F2): {len(apriori_itemsets)}")

end2_time = time.time()
duration2 = end2_time - proses2_start

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


# ========================================
# STEP 2: PRUNING DATASET UNTUK FP-GROWTH
# ========================================
proses3_start = time.time()

print("\n" + "="*60)
print("STEP 2: PRUNING DATASET UNTUK FP-GROWTH")
print("="*60)
print("Proses: Menghilangkan item-item yang tidak frequent dari transaksi.")
print("Deskripsi: Pruning adalah optimisasi untuk mengurangi ukuran dataset")
print("           dengan menghapus item yang tidak masuk dalam frequent")
print("           itemsets Apriori, sehingga FP-Growth lebih efisien.")
print("-"*60)

valid_items = set([item for sub in apriori_itemsets['itemsets'] for item in sub])
print(f"\nItem yang dianggap valid (dari Apriori): {len(valid_items)} items")
print(f"Contoh valid items: {list(valid_items)[:5]}...")

pruned_transactions = []
for trx in transactions:
    new_trx = [i for i in trx if i in valid_items]
    if new_trx:
        pruned_transactions.append(new_trx)

print(f"\nHasil Pruning:")
print(f"  - Total transaksi sebelum pruning: {len(transactions)}")
print(f"  - Total transaksi sesudah pruning: {len(pruned_transactions)}")
print(f"  - Transaksi yang dihilangkan: {len(transactions) - len(pruned_transactions)}")
print(f"  - Persentase data tersisa: {(len(pruned_transactions)/len(transactions)*100):.2f}%")
print(f"\nContoh transaksi sebelum pruning: {transactions[0][:3]}...")
print(f"Contoh transaksi sesudah pruning: {pruned_transactions[0][:3] if pruned_transactions else 'N/A'}...")

end3_time = time.time()
duration3 = end3_time - proses3_start

# Format output durasi
if duration3 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration3:.2f} detik")
else:
    duration3_ms = duration3 * 1000
    print(f"⏱️  Waktu eksekusi: {duration3_ms:.2f} milidetik")

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


# ========================================
# STEP 3: FP-GROWTH UNTUK ITEMSET ≥3
# ========================================
process4_start = time.time()

print("\n" + "="*60)
print("STEP 3: FP-GROWTH UNTUK ITEMSET >= 3")
print("="*60)
print("Proses: Mencari frequent itemsets dengan 3 atau lebih items.")
print("Deskripsi: FP-Growth adalah algoritma yang lebih efisien dari Apriori")
print("           karena menggunakan FP-Tree. Minimum support: 5 transaksi")
print("-"*60)

# Minimum support count (misal: 5 transaksi)
min_support_count = 5
print(f"Minimum support count: {min_support_count} transaksi")
print(f"Minimum support percentage: {(min_support_count/len(pruned_transactions)*100):.2f}%")

patterns = pyfpgrowth.find_frequent_patterns(pruned_transactions, min_support_count)
print(f"\nJumlah frequent patterns ditemukan: {len(patterns)}")

# convert fp-growth format → daftar itemset & support
fpg_itemsets = []
total = len(pruned_transactions)

for items, sup_count in patterns.items():
    support = sup_count / total
    fpg_itemsets.append([items, support])

fpg_df = pd.DataFrame(fpg_itemsets, columns=["itemsets", "support"])

print(f"\nHasil FP-Growth:")
print(f"  - Total itemsets FP-Growth (>= 3 items): {len(fpg_df)}")
if len(fpg_df) > 0:
    print(f"\nContoh itemsets FP-Growth (top 5):")
    print(fpg_df.head(5).to_string(index=False))
else:
    print("  - Tidak ada itemsets dengan 3 atau lebih items yang frequent")

process4_end = time.time()
duration4 = process4_end - process4_start

# Format output durasi
if duration4 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration4:.2f} detik")
else:
    duration4_ms = duration4 * 1000
    print(f"⏱️  Waktu eksekusi: {duration4_ms:.2f} milidetik")

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


# ========================================
# STEP 4: GABUNG APRIORI + FP-GROWTH
# ========================================
process5_start = time.time()

print("\n" + "="*60)
print("STEP 4: GABUNG APRIORI + FP-GROWTH (HYBRID MINING)")
print("="*60)
print("Proses: Menggabungkan hasil Apriori dan FP-Growth.")
print("Deskripsi: Hybrid mining menggabungkan kekuatan kedua algoritma:")
print("           - Apriori: itemsets 1 dan 2 items (akurat)")
print("           - FP-Growth: itemsets 3+ items (efisien)")
print("           Hasil gabungan memberikan frequent itemsets yang lengkap.")
print("-"*60)

hybrid = pd.concat([apriori_itemsets, fpg_df], ignore_index=True)

print(f"\nHasil Hybrid Mining:")
print(f"  - Itemsets dari Apriori (F1+F2): {len(apriori_itemsets)}")
print(f"  - Itemsets dari FP-Growth (>=3): {len(fpg_df)}")
print(f"  - Total itemsets hybrid: {len(hybrid)}")

# Analisis itemsets berdasarkan ukuran
itemset_sizes = hybrid['itemsets'].apply(lambda x: len(x))
print(f"\nDistribusi itemsets berdasarkan jumlah items:")
for size in sorted(itemset_sizes.unique()):
    count = (itemset_sizes == size).sum()
    print(f"  - {size} items: {count} itemsets")

print(f"\nContoh itemsets hybrid (top 10):")
print(hybrid.head(10).to_string(index=False))

process5_end = time.time()
duration5 = process5_end - process5_start

# Format output durasi
if duration5 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration5:.2f} detik")
else:
    duration5_ms = duration5 * 1000
    print(f"⏱️  Waktu eksekusi: {duration5_ms:.2f} milidetik")

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


# ========================================
# SAVE OUTPUT
# ========================================
print("\n" + "="*60)
print("SAVE OUTPUT")
print("="*60)
# Pastikan itemsets berupa list dan format string list
hybrid['itemsets'] = hybrid['itemsets'].apply(lambda x: list(x) if not isinstance(x, list) else x)
hybrid['itemsets'] = hybrid['itemsets'].apply(lambda x: repr(x))
output_filename = f"frequent_itemsets_hybrid_{datetime.now().strftime('%d%b%Y')}.csv"
hybrid.to_csv(output_filename, index=False)
print(f"✓ File berhasil disimpan: {output_filename}")
print(f"  - Total baris: {len(hybrid)}")
print(f"  - Lokasi: {output_filename}")
print("="*60)
print("Program selesai!")
totalduration = duration1 + duration2 + duration3 + duration4 + duration5
if totalduration >= 1:
    print(f"⏱️  Total waktu eksekusi: {totalduration:.2f} detik")
else:
    totalduration_ms = totalduration * 1000
    print(f"⏱️  Total waktu eksekusi: {totalduration_ms:.2f} milidetik")
print("="*60)
