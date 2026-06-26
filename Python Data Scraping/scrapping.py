import requests
import csv
import time
from datetime import datetime

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

start_time = time.time()

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
end_time = time.time()
duration = end_time - start_time

# Format output durasi
if duration >= 1:
    print(f"⏱️  Waktu eksekusi: {duration:.2f} detik")
else:
    duration_ms = duration * 1000
    print(f"⏱️  Waktu eksekusi: {duration_ms:.2f} milidetik")
print(f"Disimpan ke: {OUTPUT_FILE}")
