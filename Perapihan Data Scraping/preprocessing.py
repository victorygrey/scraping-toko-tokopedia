import pandas as pd
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Load dataset review
df = pd.read_csv("review_gt_computer.csv")

# Siapkan stopwords dan stemmer
stop_factory = StopWordRemoverFactory()
stopwords = set(stop_factory.get_stop_words())

stem_factory = StemmerFactory()
stemmer = stem_factory.create_stemmer()

# Function preprocessing
def preprocess(text):
    if pd.isna(text):
        return ""

    # lowercase
    text = text.lower()

    # remove URL
    text = re.sub(r"http\S+|www\S+", "", text)

    # remove non-alphabet
    text = re.sub(r"[^a-zA-Z\s]", " ", text)

    # tokenization
    words = text.split()

    # remove stopwords
    words = [w for w in words if w not in stopwords]

    # stemming
    words = [stemmer.stem(w) for w in words]

    # remove very short tokens
    words = [w for w in words if len(w) > 2]

    return words

# Apply preprocessing ke semua reviewText
df["tokens"] = df["reviewText"].apply(preprocess)

# Buang transaksi yang kosong
df = df[df["tokens"].map(lambda x: len(x) > 0)]

# Simpan ke CSV
df[["reviewID", "tokens"]].to_csv("preprocessed_transactions.csv", index=False)

print("Selesai! Dataset preprocessing disimpan ke: preprocessed_transactions.csv")
