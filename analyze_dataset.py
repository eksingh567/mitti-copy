import os
import json

dataset = r'C:\Users\hp\.gemini\antigravity-ide\scratch\mitti\dataset_master'
classes = [c for c in sorted(os.listdir(dataset)) if os.path.isdir(os.path.join(dataset, c))]

counts = []
for c in classes:
    p = os.path.join(dataset, c)
    files = [f for f in os.listdir(p) if os.path.isfile(os.path.join(p, f))]
    counts.append((c, len(files)))

counts.sort(key=lambda x: x[1])

print(f'Total classes: {len(counts)}')
total = sum(c for _, c in counts)
print(f'Total images: {total}')
print(f'Average per class: {total // len(counts)}')
print(f'Min: {counts[0][1]}, Max: {counts[-1][1]}')
print(f'Median: {counts[len(counts)//2][1]}')

print('\n--- Smallest 30 classes ---')
for n, c in counts[:30]:
    print(f'  {c:6d}  {n}')

print('\n--- Largest 20 classes ---')
for n, c in counts[-20:]:
    print(f'  {c:6d}  {n}')

# Distribution buckets
buckets = [(0, 50), (50, 100), (100, 500), (500, 1000), (1000, 5000), (5000, 100000)]
print('\n--- Distribution ---')
for lo, hi in buckets:
    b = [x for x in counts if lo <= x[1] < hi]
    print(f'  {lo}-{hi}: {len(b)} classes')

# Find potential duplicates (similar names)
print('\n--- Potential duplicate classes ---')
normalized = {}
for name, cnt in counts:
    key = name.lower().replace('___', ' ').replace('_', ' ').replace('(', '').replace(')', '').strip()
    if key not in normalized:
        normalized[key] = []
    normalized[key].append((name, cnt))

for key, entries in normalized.items():
    if len(entries) > 1:
        print(f'  Duplicate group "{key}":')
        for name, cnt in entries:
            print(f'    {name}: {cnt} images')
