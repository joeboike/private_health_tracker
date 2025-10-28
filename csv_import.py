import csv, sqlite3

def import_csv(file_path, table_name):
    conn = sqlite3.connect("data/diet_tracker.db")
    cursor = conn.cursor()

    with open(file_path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(f"""
                INSERT INTO {table_name} (date, breakfast, lunch, dinner, calories, fiber, protein, weight, fat_pct, visceral_fat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['date'], row['breakfast'], row['lunch'], row['dinner'],
                row['calories'], row['fiber'], row['protein'],
                row['weight'], row['fat_pct'], row['visceral_fat']
            ))

    conn.commit()
    conn.close()