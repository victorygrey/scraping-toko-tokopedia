import requests
import csv
import time
from datetime import datetime
import pandas as pd
import re
import unidecode
import glob
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
import pyfpgrowth
from itertools import combinations


# ================================
# Tahap 1: Scraping
# ================================


# ================================
# CONFIG
# ================================
SHOP_ID = "3591739"      # GT Computer Bandung
LIMIT = 10               # Sama seperti Postman
OUTPUT_FILE = f"review_gt_computer_{datetime.now().strftime('%d%b%y')}.csv"

# Headers dari cURL
HEADERS = {
    "sec-ch-ua-platform": "\"Windows\"",
    "x-version": "a4c6963",
    "Referer": "https://www.tokopedia.com/",
    "sec-ch-ua": "\"Chromium\";v=\"142\", \"Brave\";v=\"142\", \"Not_A Brand\";v=\"99\"",
    "x-price-center": "true",
    "sec-ch-ua-mobile": "?0",
    "bd-device-id": "7576651848371783185",
    "x-source": "tokopedia-lite",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "accept": "*/*",
    "content-type": "application/json",
    "x-tkpd-lite-service": "zeus"
}

URL = "https://gql.tokopedia.com/graphql/ReviewList"

# ================================
# CREATE CSV
# ================================

start_time1 = time.time()

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "reviewID",
        "productName",
        "rating",
        "reviewTime",
        "reviewText",
        "reviewerName",
        "replyText",
    ])

    page = 1
    total = 0

    while True:

        print(f"Scraping page {page}...")
        payload = [{
            "operationName": "ReviewList",
            "variables": {
                "shopID": SHOP_ID,
                "page": page,
                "limit": LIMIT,
                "sortBy": "create_time desc",
                "filterBy": ""
            },
            "query": (
                "query ReviewList($shopID: String!, $limit: Int!, $page: Int!, "
                "$filterBy: String, $sortBy: String) { "
                "productrevGetShopReviewReadingList(shopID: $shopID, limit: $limit, "
                "page: $page, filterBy: $filterBy, sortBy: $sortBy) { "
                "list { reviewID product { productName } rating reviewTime "
                "reviewText reviewerName replyText } hasNext shopName totalReviews "
                "} }"
            )
        }]

        try:
            r = requests.post(URL, headers=HEADERS, json=payload)
            if r.status_code != 200:
                print(f"❌ HTTP Error: {r.status_code} - {r.text}")
                time.sleep(5)  # Tunggu lebih lama jika error
                continue  # Coba lagi halaman yang sama

            resp_json = r.json()
            if not resp_json or "data" not in resp_json[0]:
                print("❌ Response JSON tidak sesuai format:", resp_json)
                time.sleep(5)
                continue  # Coba lagi halaman yang sama

            data = resp_json[0]["data"]["productrevGetShopReviewReadingList"]
        except Exception as e:
            print("❌ Error menerima data:", e)
            time.sleep(5)
            continue  # Coba lagi halaman yang sama

        reviews = data.get("list", [])

        if not reviews:
            print("Tidak ada data.")
            break

        for item in reviews:
            writer.writerow([
                item.get("id") or item.get("reviewID"),
                item["product"]["productName"] if item.get("product") else "",
                item.get("rating"),
                item.get("reviewTime"),
                item.get("reviewText"),
                item.get("reviewerName"),
                item.get("replyText")
            ])
            total += 1

        print(f"✔ Page {page} OK ({len(reviews)} review)")

        if not data.get("hasNext"):
            print("Tidak ada halaman berikutnya.")
            break

        page += 1
        time.sleep(1)  # biar aman dari rate limit

print(f"Selesai! Total review berhasil diambil: {total}")
end_time1 = time.time()
duration1 = end_time1 - start_time1

# Format output durasi
if duration1 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration1:.2f} detik")
else:
    duration1_ms = duration1 * 1000
    print(f"⏱️  Waktu eksekusi: {duration1_ms:.2f} milidetik")
print(f"Disimpan ke: {OUTPUT_FILE}")


# ================================
# Tahap 2: Perapihan Data
# ================================


# =========================
# 1. LOAD DATA
# =========================
# Cari file terbaru dengan pattern review_gt_computer_*.csv
proses1_start2 = time.time()

files = glob.glob("review_gt_computer_*.csv")
latest_file = max(files, key=lambda x: datetime.strptime(x.split('_')[-1].replace('.csv', ''), '%d%b%y'))
df = pd.read_csv(latest_file)
print(f"\n{'='*60}")
print(f"PROSES 1: LOAD DATA")
print(f"{'='*60}")
print(f"File loaded: {latest_file}")
print(f"Jumlah data awal: {len(df)} baris")
print(f"\nPenjelasan: Data diload dari file CSV terbaru dengan pattern review_gt_computer_*.csv")

proses1_end2 = time.time()
duration1_2 = proses1_end2 - proses1_start2

# Format output durasi
if duration1_2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration1_2:.2f} detik")
else:
    duration1_ms_2 = duration1_2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration1_ms_2:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Melanjutkan ke proses berikutnya...\n")


# =========================
# 2. HAPUS ROW KOSONG / INVALID
# =========================
proses2_start2 = time.time()

print(f"{'='*60}")
print(f"PROSES 2: HAPUS ROW KOSONG / INVALID")
print(f"{'='*60}")
print(f"Data sebelum proses: {len(df)} baris")

# Hitung berapa yang dihapus
before_drop = len(df)
df = df.dropna(subset=["productName"])  # produk harus ada
df = df[df["productName"].str.strip() != ""]
after_drop = len(df)

print(f"Data setelah proses: {after_drop} baris")
print(f"Jumlah baris dihapus: {before_drop - after_drop} baris")
print(f"\nPenjelasan: Menghapus row dengan productName kosong atau hanya berisi whitespace")

proses2_end2 = time.time()
duration2_2 = proses2_end2 - proses2_start2

# Format output durasi
if duration2_2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration2_2:.2f} detik")
else:
    duration2_ms_2 = duration2_2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration2_ms_2:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Melanjutkan ke proses berikutnya...\n")


# =========================
# 3. NORMALISASI NAMA PRODUK
# =========================
proses3_start2 = time.time()

print(f"{'='*60}")
print(f"PROSES 3: NORMALISASI NAMA PRODUK")
print(f"{'='*60}")

def normalize_product(name):
    name = str(name)

    # lowercase
    name = name.lower()

    # hilangkan symbol aneh
    name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)

    # hapus spasi dobel
    name = re.sub(r"\s+", " ", name).strip()

    # transliterate (hilangkan aksen)
    name = unidecode.unidecode(name)

    # nama produk standar → huruf kapital semua
    return name.title()

print(f"Data sebelum normalisasi: {len(df)} baris")
print(f"Contoh sebelum normalisasi:")
print(df["productName"].head(3).tolist())

df["productName"] = df["productName"].apply(normalize_product)

print(f"\nData setelah normalisasi: {len(df)} baris")
print(f"Contoh setelah normalisasi:")
print(df["productName"].head(3).tolist())
print(f"\nPenjelasan: Normalisasi meliputi:")
print(f"  • Ubah ke lowercase")
print(f"  • Hapus simbol/karakter spesial")
print(f"  • Hapus spasi ganda")
print(f"  • Transliterasi (hilangkan aksen)")
print(f"  • Ubah ke title case (setiap kata dimulai huruf kapital)")

proses3_end2 = time.time()
duration3_2 = proses3_end2 - proses3_start2

# Format output durasi
if duration3_2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration3_2:.2f} detik")
else:
    duration3_ms_2 = duration3_2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration3_ms_2:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Melanjutkan ke proses berikutnya...\n")


# =========================
# 4. HAPUS NAMA PRODUK TIDAK VALID
# =========================
proses4_start2 = time.time()

print(f"{'='*60}")
print(f"PROSES 4: HAPUS NAMA PRODUK TIDAK VALID")
print(f"{'='*60}")

INVALID_KEYWORDS = [
    "produk", "hapus", "deleted", "not found"
]

def is_valid_product(name):
    txt = name.lower()
    return not any(kw in txt for kw in INVALID_KEYWORDS)

print(f"Data sebelum proses: {len(df)} baris")
print(f"Invalid keywords yang dicek: {INVALID_KEYWORDS}")

# Hitung berapa yang dihapus
before_invalid = len(df)
df = df[df["productName"].apply(is_valid_product)]
after_invalid = len(df)

print(f"Data setelah proses: {after_invalid} baris")
print(f"Jumlah baris dihapus: {before_invalid - after_invalid} baris")
print(f"\nPenjelasan: Menghapus produk yang nama-nya mengandung keyword invalid")
print(f"seperti 'produk', 'hapus', 'deleted', 'not found', dll")

proses4_end2 = time.time()
duration4_2 = proses4_end2 - proses4_start2

# Format output durasi
if duration4_2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration4_2:.2f} detik")
else:
    duration4_ms_2 = duration4_2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration4_ms_2:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Melanjutkan ke proses berikutnya...\n")


# =========================
# 5. DROPPING DUPLIKAT REVIEW
# =========================
proses5_start2 = time.time()

print(f"{'='*60}")
print(f"PROSES 5: DROPPING DUPLIKAT REVIEW")
print(f"{'='*60}")

print(f"Data sebelum proses: {len(df)} baris")

# Hitung berapa yang dihapus
before_dup = len(df)
df = df.drop_duplicates(subset=["reviewID"], keep="first")
after_dup = len(df)

print(f"Data setelah proses: {after_dup} baris")
print(f"Jumlah duplikat dihapus: {before_dup - after_dup} baris")
print(f"\nPenjelasan: Menghapus review yang duplikat berdasarkan reviewID")
print(f"Jika ada duplikat, hanya menyimpan yang pertama (keep='first')")

proses5_end2 = time.time()
duration5_2 = proses5_end2 - proses5_start2

# Format output durasi
if duration5_2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration5_2:.2f} detik")
else:
    duration5_ms_2 = duration5_2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration5_ms_2:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Semua tahap validasi data selesai!\n")

# Total durasi semua proses
total_duration2 = duration1_2 + duration2_2 + duration3_2 + duration4_2 + duration5_2
if total_duration2 >= 1:
    print(f"⏱️  Total waktu eksekusi semua proses: {total_duration2:.2f} detik")
else:
    total_duration_ms_2 = total_duration2 * 1000
    print(f"⏱️  Waktu eksekusi: {total_duration_ms_2:.2f} milidetik")

# =========================
# 6. SAVE REVIEW BERSIH
# =========================
df.to_csv(f"clean_review_{datetime.now().strftime('%d%b%y')}.csv", index=False)
print(f"Cleaned review saved → clean_review_{datetime.now().strftime('%d%b%y')}.csv")
print("Total review bersih:", len(df))


# =========================
# 7. BENTUK DATASET TRANSAKSI
# =========================
# Setiap reviewer bisa menghasilkan lebih dari 1 transaksi produk
transactions = df.groupby("reviewerName")["productName"].apply(list).reset_index()

transactions.to_csv(f"transactions_raw_{datetime.now().strftime('%d%b%y')}.csv", index=False)
print(f"Dataset transaksi awal saved → transactions_raw_{datetime.now().strftime('%d%b%y')}.csv")


# =========================
# 8. FLATTEN FORMAT UNTUK APRIORI/FP-GROWTH
# =========================
rows = []

for idx, row in transactions.iterrows():
    reviewer = row["reviewerName"]
    items = row["productName"]
    for item in items:
        rows.append([reviewer, item])

trans_df = pd.DataFrame(rows, columns=["TransactionID", "Item"])
trans_df.to_csv(f"transactions_{datetime.now().strftime('%d%b%y')}.csv", index=False)

print(f"Final dataset transaksi saved → transactions_{datetime.now().strftime('%d%b%y')}.csv")
print("Total baris transaksi:", len(trans_df))


# ================================
# Tahap 3: Hybrida Algoritma Apriori dan FP-Growth
# ================================


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


# ================================
# Tahap 4: Association Rules
# ================================

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