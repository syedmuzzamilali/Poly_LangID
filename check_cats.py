import csv
with open('datasets/arabic_english_raw/AR-EN Intra-word CS Corpus.txt', 'r', encoding='utf-8') as f:
    cats = set()
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            cats.add(parts[2])
print("Arabic:", cats)

with open('datasets/german_english_raw/corpus/corpus.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    cats = set()
    for row in reader:
        if row:
            cats.add(row[-1])
print("German:", cats)
