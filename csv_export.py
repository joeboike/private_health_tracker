import csv, sqlite3

def export_csv(file_path):
    conn = sqlite3.connect("data/diet_tracker.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM daily_log")
    rows = cursor.fetchall()

    with open(file_path, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([desc[0] for desc in cursor.description])
        writer.writerows(rows)

    conn.close()