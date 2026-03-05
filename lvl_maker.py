import csv

height = 18          # 18 wierszy
width = 138          # 138 kolumn

rows = []
for r in range(height):
    if r == height - 1:
        # ostatni wiersz: 137 bloków podłogi + End
        row = ["0"] * 137 + ["End"]
    else:
        # pozostałe wiersze: 137 pustych (-1) + End w kolumnie 138
        row = ["-1"] * 137 + ["End"]
    rows.append(row)

with open("level_3.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print("Utworzono level_3.csv: 18 wierszy × 138 kolumn")
print("Kolumna 138 = End we wszystkich wierszach")
print("Kolumn 1-137 = podłoga tylko w dolnym wierszu, reszta -1")
