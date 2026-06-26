import pandas as pd
import re
import unidecode
import glob
import time
from datetime import datetime

# =========================
# 1. LOAD DATA
# =========================
# Cari file terbaru dengan pattern review_gt_computer_*.csv
proses1_start = time.time()

files = glob.glob("review_gt_computer_*.csv")
latest_file = max(files, key=lambda x: datetime.strptime(x.split('_')[-1].replace('.csv', ''), '%d%b%y'))
df = pd.read_csv(latest_file)
print(f"\n{'='*60}")
print(f"PROSES 1: LOAD DATA")
print(f"{'='*60}")
print(f"File loaded: {latest_file}")
print(f"Jumlah data awal: {len(df)} baris")
print(f"\nPenjelasan: Data diload dari file CSV terbaru dengan pattern review_gt_computer_*.csv")

proses1_end = time.time()
duration1 = proses1_end - proses1_start

# Format output durasi
if duration1 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration1:.2f} detik")
else:
    duration1_ms = duration1 * 1000
    print(f"⏱️  Waktu eksekusi: {duration1_ms:.2f} milidetik")

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
proses2_start = time.time()

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

proses2_end = time.time()
duration2 = proses2_end - proses2_start

# Format output durasi
if duration2 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration2:.2f} detik")
else:
    duration2_ms = duration2 * 1000
    print(f"⏱️  Waktu eksekusi: {duration2_ms:.2f} milidetik")

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
proses3_start = time.time()

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

proses3_end = time.time()
duration3 = proses3_end - proses3_start

# Format output durasi
if duration3 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration3:.2f} detik")
else:
    duration3_ms = duration3 * 1000
    print(f"⏱️  Waktu eksekusi: {duration3_ms:.2f} milidetik")

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
proses4_start = time.time()

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

proses4_end = time.time()
duration4 = proses4_end - proses4_start

# Format output durasi
if duration4 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration4:.2f} detik")
else:
    duration4_ms = duration4 * 1000
    print(f"⏱️  Waktu eksekusi: {duration4_ms:.2f} milidetik")

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
proses5_start = time.time()

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

proses5_end = time.time()
duration5 = proses5_end - proses5_start

# Format output durasi
if duration5 >= 1:
    print(f"⏱️  Waktu eksekusi: {duration5:.2f} detik")
else:
    duration5_ms = duration5 * 1000
    print(f"⏱️  Waktu eksekusi: {duration5_ms:.2f} milidetik")

# Konfirmasi sebelum lanjut
confirm = input("\nApakah ingin dilanjut? (Y/N): ").upper()
if confirm != 'Y':
    print("Proses dibatalkan!")
    exit()
else:
    print("✓ Semua tahap validasi data selesai!\n")

# Total durasi semua proses
total_duration = duration1 + duration2 + duration3 + duration4 + duration5
if total_duration >= 1:
    print(f"⏱️  Total waktu eksekusi semua proses: {total_duration:.2f} detik")
else:
    total_duration_ms = total_duration * 1000
    print(f"⏱️  Waktu eksekusi: {total_duration_ms:.2f} milidetik")

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
