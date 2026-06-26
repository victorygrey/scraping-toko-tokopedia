"""
Flask server untuk dashboard visualisasi Association Rule Mining.
Saat startup: jalankan pipeline scraping -> cleaning -> mining -> rules (otomatis).
Setelah pipeline selesai: serve website dashboard.
"""
import glob
import os
import json
import re
import ast
import sys
import time
import requests
import csv
import pandas as pd
import unidecode
from datetime import datetime
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
import pyfpgrowth
from itertools import combinations
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__, static_folder='static', template_folder='templates')


# ============================================================
#  PIPELINE FUNCTIONS (dari algoritma+scraping.py, tanpa input)
# ============================================================

def log(msg):
    print(msg, flush=True)


def pipeline_scraping():
    """Tahap 1: Scraping data dari Tokopedia GraphQL API."""
    SHOP_ID = "3591739"
    LIMIT = 10
    OUTPUT_FILE = f"review_gt_computer_{datetime.now().strftime('%d%b%y')}.csv"

    HEADERS = {
        "sec-ch-ua-platform": '"Windows"',
        "x-version": "a4c6963",
        "Referer": "https://www.tokopedia.com/",
        "sec-ch-ua": '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
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

    log(f"\n{'='*60}")
    log("TAHAP 1: SCRAPING DATA REVIEW TOKOPEDIA")
    log(f"{'='*60}")

    start_time = time.time()
    total = 0

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["reviewID", "productName", "rating", "reviewTime", "reviewText", "reviewerName", "replyText"])

        page = 1
        while True:
            log(f"Scraping page {page}...")
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
                r = requests.post(URL, headers=HEADERS, json=payload, timeout=30)
                if r.status_code != 200:
                    log(f"HTTP Error: {r.status_code} - retrying...")
                    time.sleep(5)
                    continue

                resp_json = r.json()
                if not resp_json or "data" not in resp_json[0]:
                    log(f"Response JSON tidak sesuai - retrying...")
                    time.sleep(5)
                    continue

                data = resp_json[0]["data"]["productrevGetShopReviewReadingList"]
            except Exception as e:
                log(f"Error menerima data: {e} - retrying...")
                time.sleep(5)
                continue

            reviews = data.get("list", [])
            if not reviews:
                log("Tidak ada data lagi.")
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

            log(f"  Page {page} OK ({len(reviews)} review)")

            if not data.get("hasNext"):
                log("Tidak ada halaman berikutnya.")
                break

            page += 1
            time.sleep(1)

    duration = time.time() - start_time
    log(f"\nSelesai! Total review: {total} | Waktu: {duration:.2f} detik")
    log(f"Disimpan ke: {OUTPUT_FILE}")
    return OUTPUT_FILE


def pipeline_cleaning(review_file=None):
    """Tahap 2: Pembersihan data review."""
    log(f"\n{'='*60}")
    log("TAHAP 2: PEMBERSIHAN DATA")
    log(f"{'='*60}")

    # Load file terbaru jika tidak diberikan
    if review_file is None:
        files = glob.glob("review_gt_computer_*.csv")
        if not files:
            log("Error: Tidak ada file review ditemukan!")
            return None
        review_file = max(files, key=os.path.getmtime)

    df = pd.read_csv(review_file)
    log(f"File loaded: {review_file} | Baris awal: {len(df)}")

    # 2. Hapus row kosong
    before = len(df)
    df = df.dropna(subset=["productName"])
    df = df[df["productName"].str.strip() != ""]
    log(f"Hapus kosong: {before} -> {len(df)} baris")

    # 3. Normalisasi nama produk
    def normalize_product(name):
        name = str(name).lower()
        name = re.sub(r"[^a-zA-Z0-9 ]", " ", name)
        name = re.sub(r"\s+", " ", name).strip()
        name = unidecode.unidecode(name)
        return name.title()

    df["productName"] = df["productName"].apply(normalize_product)
    log("Normalisasi nama produk selesai")

    # 4. Hapus produk invalid
    INVALID_KEYWORDS = ["produk", "hapus", "deleted", "not found"]
    def is_valid_product(name):
        txt = name.lower()
        return not any(kw in txt for kw in INVALID_KEYWORDS)

    before = len(df)
    df = df[df["productName"].apply(is_valid_product)]
    log(f"Hapus invalid: {before} -> {len(df)} baris")

    # 5. Hapus duplikat
    before = len(df)
    df = df.drop_duplicates(subset=["reviewID"], keep="first")
    log(f"Hapus duplikat: {before} -> {len(df)} baris")

    # 6. Save cleaned review
    clean_file = f"clean_review_{datetime.now().strftime('%d%b%y')}.csv"
    df.to_csv(clean_file, index=False)
    log(f"Cleaned review saved: {clean_file}")

    # 7. Bentuk dataset transaksi
    transactions = df.groupby("reviewerName")["productName"].apply(list).reset_index()
    raw_file = f"transactions_raw_{datetime.now().strftime('%d%b%y')}.csv"
    transactions.to_csv(raw_file, index=False)
    log(f"Transactions raw saved: {raw_file}")

    # 8. Flatten format
    rows = []
    for _, row in transactions.iterrows():
        for item in row["productName"]:
            rows.append([row["reviewerName"], item])

    trans_df = pd.DataFrame(rows, columns=["TransactionID", "Item"])
    trans_file = f"transactions_{datetime.now().strftime('%d%b%y')}.csv"
    trans_df.to_csv(trans_file, index=False)
    log(f"Flattened transactions saved: {trans_file} | Total baris: {len(trans_df)}")

    return trans_file, raw_file


def pipeline_mining(transactions_raw_file=None):
    """Tahap 3: Hybrid Mining (Apriori + FP-Growth)."""
    log(f"\n{'='*60}")
    log("TAHAP 3: HYBRID MINING (APRIORI + FP-GROWTH)")
    log(f"{'='*60}")

    if transactions_raw_file is None:
        files = glob.glob("transactions_raw_*.csv")
        if not files:
            log("Error: Tidak ada file transactions_raw ditemukan!")
            return None
        transactions_raw_file = max(files, key=os.path.getmtime)

    df = pd.read_csv(transactions_raw_file)
    transactions = df["productName"].apply(lambda x: x.strip("[]").split(","))
    transactions = [[i.strip().strip("'").strip('"') for i in row] for row in transactions]
    log(f"Transaksi dimuat: {len(transactions)} transaksi")

    # STEP 1: Apriori F1 & F2
    te = TransactionEncoder()
    te_data = te.fit(transactions).transform(transactions)
    df_ap = pd.DataFrame(te_data, columns=te.columns_)
    log(f"Matrix Apriori: {df_ap.shape[0]} x {df_ap.shape[1]} items")

    F1 = apriori(df_ap, min_support=0.01, use_colnames=True)
    F2 = apriori(df_ap, min_support=0.01, use_colnames=True, max_len=2)
    apriori_itemsets = pd.concat([F1, F2])
    log(f"Apriori: F1={len(F1)}, F2={len(F2)}, total={len(apriori_itemsets)}")

    # STEP 2: Pruning
    valid_items = set([item for sub in apriori_itemsets['itemsets'] for item in sub])
    pruned_transactions = []
    for trx in transactions:
        new_trx = [i for i in trx if i in valid_items]
        if new_trx:
            pruned_transactions.append(new_trx)
    log(f"Pruning: {len(transactions)} -> {len(pruned_transactions)} transaksi")

    # STEP 3: FP-Growth >= 3
    min_support_count = 5
    patterns = pyfpgrowth.find_frequent_patterns(pruned_transactions, min_support_count)
    total = len(pruned_transactions)
    fpg_itemsets = []
    for items, sup_count in patterns.items():
        support = sup_count / total
        fpg_itemsets.append([items, support])

    fpg_df = pd.DataFrame(fpg_itemsets, columns=["itemsets", "support"])
    log(f"FP-Growth (>=3 items): {len(fpg_df)} itemset")

    # STEP 4: Gabung
    hybrid = pd.concat([apriori_itemsets, fpg_df], ignore_index=True)
    log(f"Hybrid total: {len(hybrid)} itemset")

    # Save
    hybrid['itemsets'] = hybrid['itemsets'].apply(lambda x: list(x) if not isinstance(x, list) else x)
    hybrid['itemsets'] = hybrid['itemsets'].apply(lambda x: repr(x))
    output_file = f"frequent_itemsets_hybrid_{datetime.now().strftime('%d%b%Y')}.csv"
    hybrid.to_csv(output_file, index=False)
    log(f"Frequent itemsets saved: {output_file}")

    return output_file


def pipeline_rules(freq_file=None):
    """Tahap 4: Generate Association Rules."""
    log(f"\n{'='*60}")
    log("TAHAP 4: GENERATE ASSOCIATION RULES")
    log(f"{'='*60}")

    if freq_file is None:
        files = glob.glob("frequent_itemsets_hybrid*.csv")
        if not files:
            log("Error: Tidak ada file frequent_itemsets_hybrid ditemukan!")
            return None
        freq_file = max(files, key=os.path.getmtime)

    df = pd.read_csv(freq_file)
    itemset_col = "itemsets"

    def parse_itemset(x):
        val = ast.literal_eval(x) if isinstance(x, str) else x
        if isinstance(val, tuple):
            val = list(val)
        return val

    df[itemset_col] = df[itemset_col].apply(parse_itemset)
    support_dict = {
        tuple(sorted(items)): support
        for items, support in zip(df[itemset_col], df["support"])
    }
    log(f"Itemsets dimuat: {len(support_dict)}")

    # Generate rules
    rules = []
    for itemset, support_itemset in support_dict.items():
        if len(itemset) < 2:
            continue
        for i in range(1, len(itemset)):
            for antecedent in combinations(itemset, i):
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

    log(f"Total rules dihasilkan: {len(rules)}")

    # Save
    rules_df = pd.DataFrame(rules)
    if not rules_df.empty:
        rules_df['antecedent'] = rules_df['antecedent'].apply(lambda x: list(x) if not isinstance(x, list) else x)
        rules_df['antecedent'] = rules_df['antecedent'].apply(lambda x: repr(x))
        rules_df['consequent'] = rules_df['consequent'].apply(lambda x: list(x) if not isinstance(x, list) else x)
        rules_df['consequent'] = rules_df['consequent'].apply(lambda x: repr(x))

    output_file = f"association_rules_hybrid_{datetime.now().strftime('%d%b%Y')}.csv"
    rules_df.to_csv(output_file, index=False)
    log(f"Association rules saved: {output_file}")

    return output_file


def run_full_pipeline():
    """Jalankan seluruh pipeline secara otomatis."""
    log("\n" + "=" * 70)
    log("  MEMULAI FULL PIPELINE: Scraping → Cleaning → Mining → Rules")
    log("=" * 70)

    t0 = time.time()

    try:
        # Tahap 1: Scraping
        review_file = pipeline_scraping()

        # Tahap 2: Cleaning
        trans_file, raw_file = pipeline_cleaning(review_file)

        # Tahap 3: Mining
        freq_file = pipeline_mining(raw_file)

        # Tahap 4: Rules
        rules_file = pipeline_rules(freq_file)

        duration = time.time() - t0
        log(f"\n{'='*70}")
        log(f"  PIPELINE SELESAI! Total waktu: {duration:.2f} detik")
        log(f"{'='*70}\n")

        return rules_file
    except Exception as e:
        log(f"\n❌ PIPELINE ERROR: {e}")
        import traceback
        traceback.print_exc()
        log("\n⚠️  Pipeline gagal. Akan mencoba membaca file CSV yang sudah ada...")
        return None


# ============================================================
#  FLASK API ENDPOINTS
# ============================================================

def get_latest_csv(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def get_today_csv(pattern):
    """Cari file CSV yang tanggalnya sesuai hari ini (berdasarkan nama file)."""
    today = datetime.now()
    today_str_short = today.strftime('%d%b%y')    # e.g. 26Jun25
    today_str_long = today.strftime('%d%b%Y')      # e.g. 26Jun2025

    files = glob.glob(pattern)
    matching = []
    for f in files:
        basename = os.path.basename(f).lower()
        if today_str_short.lower() in basename or today_str_long.lower() in basename:
            matching.append(f)

    if matching:
        return max(matching, key=os.path.getmtime)
    return None


def parse_csv_value(val):
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return [val]
    return val if isinstance(val, list) else [val]


@app.route('/')
def index():
    with open(os.path.join(app.static_folder, 'index.html'), 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/api/summary')
def api_summary():
    freq_file = get_today_csv('frequent_itemsets_hybrid_*.csv') or get_latest_csv('frequent_itemsets_hybrid_*.csv')
    rules_file = get_today_csv('association_rules_hybrid_*.csv') or get_latest_csv('association_rules_hybrid_*.csv')

    summary = {
        'freq_itemsets_file': os.path.basename(freq_file) if freq_file else None,
        'rules_file': os.path.basename(rules_file) if rules_file else None,
    }

    if freq_file:
        df = pd.read_csv(freq_file)
        sizes = df['itemsets'].apply(lambda x: len(parse_csv_value(x)))
        size_dist = sizes.value_counts().sort_index().to_dict()
        summary['total_itemsets'] = len(df)
        summary['itemset_size_distribution'] = {str(k): v for k, v in size_dist.items()}

    if rules_file:
        df = pd.read_csv(rules_file)
        summary['total_rules'] = len(df)
        if len(df) > 0:
            summary['avg_support'] = round(float(df['support'].mean()), 4)
            summary['avg_confidence'] = round(float(df['confidence'].mean()), 4)
            summary['avg_lift'] = round(float(df['lift'].mean()), 4)
            summary['max_support'] = round(float(df['support'].max()), 4)
            summary['max_confidence'] = round(float(df['confidence'].max()), 4)
            summary['max_lift'] = round(float(df['lift'].max()), 4)

    return jsonify(summary)


@app.route('/api/top-items')
def api_top_items():
    freq_file = get_today_csv('frequent_itemsets_hybrid_*.csv') or get_latest_csv('frequent_itemsets_hybrid_*.csv')
    if not freq_file:
        return jsonify({'error': 'No data found'})

    df = pd.read_csv(freq_file)
    df['itemsets'] = df['itemsets'].apply(lambda x: parse_csv_value(x))
    df['size'] = df['itemsets'].apply(len)

    singles = df[df['size'] == 1].nlargest(15, 'support')
    top_singles = [{'item': row['itemsets'][0], 'support': round(float(row['support']), 4)} for _, row in singles.iterrows()]

    combos = df[df['size'] >= 2].nlargest(15, 'support')
    top_combos = [{'combination': ' + '.join(row['itemsets']), 'support': round(float(row['support']), 4), 'size': int(row['size'])} for _, row in combos.iterrows()]

    return jsonify({'top_single_items': top_singles, 'top_combinations': top_combos})


@app.route('/api/top-rules')
def api_top_rules():
    rules_file = get_today_csv('association_rules_hybrid_*.csv') or get_latest_csv('association_rules_hybrid_*.csv')
    if not rules_file:
        return jsonify({'error': 'No data found'})

    df = pd.read_csv(rules_file)
    df['antecedent'] = df['antecedent'].apply(lambda x: parse_csv_value(x))
    df['consequent'] = df['consequent'].apply(lambda x: parse_csv_value(x))

    def format_rules(rules_df):
        result = []
        for _, row in rules_df.iterrows():
            result.append({
                'antecedent': ' + '.join(row['antecedent']),
                'consequent': ' + '.join(row['consequent']),
                'support': round(float(row['support']), 4),
                'confidence': round(float(row['confidence']), 4),
                'lift': round(float(row['lift']), 4),
            })
        return result

    return jsonify({
        'top_by_lift': format_rules(df.nlargest(15, 'lift')),
        'top_by_confidence': format_rules(df.nlargest(15, 'confidence'))
    })


@app.route('/api/distribution')
def api_distribution():
    rules_file = get_today_csv('association_rules_hybrid_*.csv') or get_latest_csv('association_rules_hybrid_*.csv')
    if not rules_file:
        return jsonify({'error': 'No data found'})

    df = pd.read_csv(rules_file)
    support_bins = [0, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.5, 1.0]
    confidence_bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    lift_bins = [0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0]

    def histogram_data(series, bins):
        counts = pd.Series(series).value_counts(bins=bins, sort=False)
        result = []
        for interval, count in counts.items():
            low = interval.left
            high = interval.right
            result.append({'range': f'{low:.2f}–{high:.2f}', 'count': int(count)})
        return result

    return jsonify({
        'support_dist': histogram_data(df['support'], support_bins),
        'confidence_dist': histogram_data(df['confidence'], confidence_bins),
        'lift_dist': histogram_data(df['lift'], lift_bins),
    })


@app.route('/api/category-pie')
def api_category_pie():
    freq_file = get_today_csv('frequent_itemsets_hybrid_*.csv') or get_latest_csv('frequent_itemsets_hybrid_*.csv')
    if not freq_file:
        return jsonify({'error': 'No data found'})

    df = pd.read_csv(freq_file)
    df['itemsets'] = df['itemsets'].apply(lambda x: parse_csv_value(x))
    singles = df[df['itemsets'].apply(len) == 1]

    categories = {
        'SSD / Storage': ['ssd', 'hardisk', 'hdd', 'nvme', 'sata', 'storage', 'legend', 'm.2'],
        'RAM / Memory': ['ram', 'memory', 'ddr', 'hynix', 'corsair', 'sodimm'],
        'VGA / GPU': ['vga', 'gtx', 'gpu', 'vurrion', 'graphics'],
        'Processor / CPU': ['intel', 'amd', 'ryzen', 'core i', 'processor', 'cpu'],
        'PSU / Power Supply': ['psu', 'watt', 'power supply', 'modular', '80 plus'],
        'Motherboard': ['motherboard', 'mobo', 'mainboard', 'h610', 'b550', 'b450'],
        'Monitor / Display': ['monitor', 'led', 'lcd', 'display'],
        'PC Rakitan / Fullset': ['pc rakitan', 'pc gaming', 'fullset', 'komputer mini'],
        'Aksesoris / Packing': ['packing', 'buble', 'fan', 'casing', 'caddy', 'kabel', 'baut'],
        'Networking': ['router', 'wifi', 'lan', 'modem', 'rj45', 'access point'],
        'Lainnya': [],
    }

    category_counts = {cat: 0 for cat in categories}
    for _, row in singles.iterrows():
        item = row['itemsets'][0].lower()
        categorized = False
        for cat, keywords in categories.items():
            if any(kw in item for kw in keywords):
                category_counts[cat] += 1
                categorized = True
                break
        if not categorized:
            category_counts['Lainnya'] += 1

    category_counts = {k: v for k, v in category_counts.items() if v > 0}
    return jsonify({'categories': category_counts})


# ============================================================
#  MAIN: Jalankan pipeline dulu, baru serve web
# ============================================================

if __name__ == '__main__':
    log("\n" + "=" * 70)
    log("  ASSOCIATION RULE MINING DASHBOARD")
    log("  Pipeline + Web Server")
    log("=" * 70)

    # Cek apakah sudah ada file CSV hari ini
    existing_rules = get_today_csv('association_rules_hybrid_*.csv')
    existing_freq = get_today_csv('frequent_itemsets_hybrid_*.csv')

    # Fallback ke file terbaru jika tidak ada file hari ini
    if not existing_rules:
        existing_rules = get_latest_csv('association_rules_hybrid_*.csv')
    if not existing_freq:
        existing_freq = get_latest_csv('frequent_itemsets_hybrid_*.csv')

    if existing_rules and existing_freq:
        is_today = get_today_csv('association_rules_hybrid_*.csv') is not None
        if is_today:
            log(f"\nFile CSV hari ini ditemukan:")
        else:
            log(f"\nFile CSV hari ini tidak ditemukan. Menggunakan file terbaru:")
        log(f"  - {existing_rules}")
        log(f"  - {existing_freq}")
        log(f"\nApakah ingin jalankan pipeline scraping ulang? (y/n)")
        log(f"(Tekan 'n' untuk langsung gunakan data yang ada)")

        # Di mode non-interaktif (Docker), langsung gunakan data existing
        # Di mode interaktif, bisa override
        use_existing = True
        if sys.stdin.isatty():
            try:
                choice = input("> ").strip().lower()
                use_existing = (choice != 'y')
            except (EOFError, KeyboardInterrupt):
                use_existing = True
        else:
            # Non-interactive (Docker/CI): langsung serve existing
            use_existing = True
            log("\nMode non-interactive: menggunakan data CSV yang sudah ada.")

        if not use_existing:
            run_full_pipeline()
    else:
        log("\nTidak ada file CSV yang ditemukan. Menjalankan pipeline...")
        run_full_pipeline()

    log("\n" + "=" * 70)
    log("  MEMULAI WEB SERVER")
    log("  Dashboard tersedia di: http://localhost:8000")
    log("=" * 70 + "\n")

    app.run(host='0.0.0.0', port=8000, debug=False)
