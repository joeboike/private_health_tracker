import sqlite3

conn = sqlite3.connect("data/diet_tracker.db")
c = conn.cursor()

# Patch the ingredient
c.execute("UPDATE ingredients SET protein_g = 0, fat_g = 0 WHERE name = ?", ("Jam, (average)",))
c.execute("UPDATE ingredients SET fiber_g = 0, fat_g = 4 WHERE name = ?", ("Egg, Large",))

conn.commit()
conn.close()