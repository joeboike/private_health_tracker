import sqlite3

conn = sqlite3.connect("data/diet_tracker.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS body_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    weight REAL,
    body_fat REAL,
    visceral_fat REAL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_log (
    id INTEGER PRIMARY KEY,
    date TEXT,
    breakfast TEXT,
    lunch TEXT,
    dinner TEXT,
    calories REAL,
    fiber REAL,
    protein REAL,
    weight REAL,
    fat_pct REAL,
    visceral_fat REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    calories REAL,
    protein_g REAL,
    fiber_g REAL,
    fat_g REAL,
    carbs_g REAL,
    notes TEXT
)
""")

# Create recipes table
cursor.execute("""
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    notes TEXT
)
""")

# Create recipe_items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS recipe_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    unit TEXT,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
)
""")

# Create recipe_items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS menus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date TEXT,
    notes TEXT
)
""")

# Create recipe_items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS menu_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    portion REAL DEFAULT 1.0,
    FOREIGN KEY (menu_id) REFERENCES menus(id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id)
)
""")

# Create recipe_items table
cursor.execute("""
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER NOT NULL,
    ingredient_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    unit TEXT,
    FOREIGN KEY (menu_id) REFERENCES menus(id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
)
""")
               
conn.commit()
conn.close()