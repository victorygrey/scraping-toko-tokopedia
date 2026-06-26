# 📊 Scraping Toko Tokopedia — Hybrid Association Rule Mining

Pipeline data mining lengkap yang melakukan scraping ulasan produk dari Tokopedia, pembersihan data, dan penerapan **Hybrid Association Rule Mining** (Apriori + FP-Growth) untuk menemukan pola pembelian pelanggan, dilengkapi **dashboard web interaktif**.

---

## 🎯 Tujuan

Menemukan **aturan asosiasi** antar produk yang sering dibeli bersamaan oleh pelanggan toko **GT Computer Bandung** di Tokopedia, menggunakan kombinasi algoritma:

| Algoritma     | Digunakan Untuk                                                                |
| ------------- | ------------------------------------------------------------------------------ |
| **Apriori**   | Mencari frequent itemset berukuran 1 dan 2 item (akurat untuk kombinasi kecil) |
| **FP-Growth** | Mencari frequent itemset berukuran 3+ item (efisien untuk kombinasi besar)     |

Hasilnya berupa aturan: _"Jika pelanggan beli A, maka cenderung beli B"_ dengan metrik **support**, **confidence**, dan **lift**.

---

## 🏗️ Arsitektur Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 1: SCRAPING                                              │
│  File: algoritma+scraping.py (bagian scraping)                  │
│  Input:  API GraphQL Tokopedia                                  │
│  Output: review_gt_computer_DDMonYY.csv                         │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 2: CLEANING                                              │
│  File: algoritma+scraping.py (bagian cleaning)                  │
│  Input:  review_gt_computer_*.csv                               │
│  Proses: Hapus kosong → Normalisasi → Filter → Deduplikasi      │
│  Output: clean_review_*.csv, transactions_raw_*.csv,             │
│          transactions_*.csv                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 3: HYBRID MINING                                         │
│  File: algoritma+scraping.py (bagian mining)                    │
│  Input:  transactions_raw_*.csv                                 │
│  Proses: Apriori (F1+F2) → Pruning → FP-Growth (≥3) → Gabung   │
│  Output: frequent_itemsets_hybrid_DDMonYYYY.csv                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 4: ASSOCIATION RULES                                     │
│  File: algoritma+scraping.py (bagian rules)                     │
│  Input:  frequent_itemsets_hybrid_*.csv                         │
│  Proses: Generate rules → Hitung confidence & lift              │
│  Output: association_rules_hybrid_DDMonYYYY.csv                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TAHAP 5: DASHBOARD WEB                                         │
│  File: app.py + static/index.html                               │
│  Fitur: Bar chart, Pie chart, Histogram, Tabel interaktif       │
│  Output: Dashboard di http://localhost:8000                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktur Proyek

```
scraping-toko-tokopedia/
├── app.py                          # Flask server + Pipeline otomatis + Dashboard API
├── algoritma+scraping.py           # Pipeline lengkap (standalone, interaktif)
├── requirements.txt                # Dependensi Python
├── Dockerfile                      # Konfigurasi Docker
├── compose.yaml                    # Docker Compose
├── static/
│   └── index.html                  # Dashboard web interaktif (Chart.js)
├── Python Data Scraping/           # Script scraping individual (arsip)
├── Perapihan Data Scraping/        # Script cleaning individual (arsip)
└── Hybrid Algoritma Apriori dan FP-Growth/  # Script mining individual (arsip)
```

---

## 🚀 Cara Menjalankan

### Opsi 1: Docker (Recommended)

```bash
# Build dan jalankan
docker compose up --build

# Dashboard tersedia di:
# http://localhost:8000
```

Dalam mode Docker, aplikasi akan:

1. Menggunakan file CSV yang sudah ada (jika ada)
2. Langsung serve dashboard web

### Opsi 2: Lokal (Python)

```bash
# 1. Install dependensi
pip install -r requirements.txt

# 2. Jalankan aplikasi
python app.py
```

Dalam mode lokal interaktif, kamu akan ditanya apakah ingin:

- Menjalankan pipeline scraping ulang (ketik `y`)
- Langsung menggunakan data CSV yang sudah ada (ketik `n`)

### Opsi 3: Jalankan Pipeline Saja (Tanpa Web)

```bash
python "algoritma+scraping.py"
```

Script ini akan menjalankan pipeline lengkap dengan konfirmasi manual di setiap tahap.

---

## 📊 Dataset

| Keterangan          | Nilai                                        |
| ------------------- | -------------------------------------------- |
| **Sumber Data**     | Ulasan toko GT Computer Bandung di Tokopedia |
| **Shop ID**         | 3591739                                      |
| **Total Review**    | ~2.819 review bersih                         |
| **Reviewer Unik**   | 1.230 reviewer                               |
| **Produk Unik**     | 753 produk                                   |
| **Baris Transaksi** | 2.314 baris                                  |

### Format Output CSV

**`association_rules_hybrid_*.csv`**
| Kolom | Deskripsi |
|---|---|
| `antecedent` | Produk yang menjadi pemicu ("Jika beli...") |
| `consequent` | Produk yang ikut dibeli ("...maka juga beli") |
| `support` | Seberapa sering kombinasi muncul di seluruh transaksi |
| `confidence` | Probabilitas: jika beli antecedent, berapa % beli consequent |
| `lift` | Kekuatan korelasi (>1 = positif, =1 = netral, <1 = negatif) |

**`frequent_itemsets_hybrid_*.csv`**
| Kolom | Deskripsi |
|---|---|
| `itemsets` | Kombinasi produk yang sering muncul bersama |
| `support` | Frekuensi kemunculan kombinasi tersebut |

---

## 🖥️ Fitur Dashboard

Dashboard web menyediakan visualisasi interaktif:

| Fitur                    | Deskripsi                                           |
| ------------------------ | --------------------------------------------------- |
| **📈 Summary Cards**     | Ringkasan total itemsets, rules, rata-rata metrik   |
| **🥧 Pie Chart**         | Distribusi kategori produk (SSD, RAM, VGA, dll.)    |
| **📏 Bar Chart**         | Distribusi ukuran itemset (1 item, 2 item, 3+ item) |
| **📊 Histogram**         | Distribusi support, confidence, dan lift            |
| **🏆 Top Items**         | 15 produk paling populer & 15 kombinasi terpopuler  |
| **🔗 Association Rules** | Tabel rules terkuat berdasarkan lift & confidence   |

### Tab Dashboard

1. **Overview** — Grafik dan statistik umum
2. **Top Items** — Produk dan kombinasi terpopuler
3. **Association Rules** — Tabel detail aturan asosiasi

---

## ⚙️ Teknologi

| Komponen            | Teknologi                                     |
| ------------------- | --------------------------------------------- |
| **Scraping**        | `requests`, GraphQL API Tokopedia             |
| **Data Processing** | `pandas`, `unidecode`                         |
| **Mining**          | `mlxtend` (Apriori), `pyfpgrowth` (FP-Growth) |
| **Web Server**      | Flask                                         |
| **Frontend**        | HTML, CSS, Chart.js                           |
| **Container**       | Docker, Docker Compose                        |

---

## 📝 Catatan Penting

- **Headers API** menggunakan browser fingerprint yang mungkin kadaluarsa. Jika scraping gagal, update headers dari browser DevTools.
- **Rate limiting** sudah ditangani dengan `time.sleep(1)` antar halaman.
- File CSV lama disimpan sebagai arsip — setiap run menghasilkan file bertanda tanggal baru.
- Dashboard memprioritaskan file CSV **hari ini**, fallback ke file **terbaru** jika tidak ada.

---

## 📄 Lisensi

Proyek ini dibuat oleh Faizal Hamzah untuk keperluan edukasi dan riset data mining.

---

Thanks to :

> **GT Computer Bandung** — Toko komponen komputer & IT di Tokopedia
