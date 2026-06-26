import re

# Baca file
with open('scrapping.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Cari baris 'with open(OUTPUT_FILE'
insert_idx = None
for i, line in enumerate(lines):
    if 'with open(OUTPUT_FILE' in line:
        insert_idx = i
        break

if insert_idx is not None:
    # Tambah start_time sebelum with open
    lines.insert(insert_idx, 'start_time = time.time()\n')
    lines.insert(insert_idx + 1, '\n')

# Cari baris terakhir 'print(f"Selesai! Total review..."
for i in range(len(lines) - 1, -1, -1):
    if 'Selesai! Total review berhasil diambil' in lines[i]:
        # Tambah waktu eksekusi setelah ini
        end_idx = i + 1
        timer_code = '''end_time = time.time()
duration = end_time - start_time

# Format output durasi
if duration >= 1:
    print(f"⏱️  Waktu eksekusi: {duration:.2f} detik")
else:
    duration_ms = duration * 1000
    print(f"⏱️  Waktu eksekusi: {duration_ms:.2f} milidetik")
'''
        lines.insert(end_idx, timer_code)
        break

# Tulis kembali file
with open('scrapping.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✓ File scrapping.py berhasil diupdate dengan timer!')
