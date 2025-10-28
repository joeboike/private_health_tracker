from flask import Flask, render_template, request, redirect, flash, session
from datetime import date, timedelta
import json
import sqlite3

app = Flask(__name__)
app.secret_key = "My_$up3r_$3cr3t_K3y"  # Needed for flashing messagesimport sqlite3

@app.route("/log/meals", methods=["GET", "POST"])
def log_meals():
    if request.method == "POST":
        date = request.form["date"]
        breakfast = request.form["breakfast"]
        lunch = request.form["lunch"]
        dinner = request.form["dinner"]
        print("Meals logged:", date, breakfast, lunch, dinner)
        return redirect("/log/metrics")
    return render_template("log_meals.html")

@app.route("/log/metrics", methods=["GET", "POST"])
def log_metrics():
    if request.method == "POST":
        date = request.form["date"]
        weight = request.form["weight"]
        body_fat = request.form["body_fat"]
        visceral_fat = request.form["visceral_fat"]

        conn = sqlite3.connect("data/diet_tracker.db")
        c = conn.cursor()

        # Check if entry for this date already exists
        c.execute("SELECT * FROM body_metrics WHERE date = ?", (date,))
        existing = c.fetchone()

        if existing:
            session["pending_entry"] = {
                "date": date,
                "weight": weight,
                "body_fat": body_fat,
                "visceral_fat": visceral_fat
            }
            session["existing_entry"] = {
                "date": existing[1],
                "weight": existing[2],
                "body_fat": existing[3],
                "visceral_fat": existing[4]
            }
            return redirect("/confirm_overwrite")
        
        # Get previous entry
        c.execute("""
            SELECT weight, body_fat, visceral_fat
            FROM body_metrics
            WHERE date < ?
            ORDER BY date DESC
            LIMIT 1
        """, (date,))
        previous = c.fetchone()

        # Compare and flash alerts
        thresholds_exceeded = []
        if previous:
            prev_weight, prev_body_fat, prev_visc_fat = previous
            if abs(float(weight) - prev_weight) > 5:
                thresholds_exceeded.append("Weight")
            if abs(float(body_fat) - prev_body_fat) > 3:
                thresholds_exceeded.append("Body Fat")
            if abs(float(visceral_fat) - prev_visc_fat) > 3:
                thresholds_exceeded.append("Visceral Fat")

            if thresholds_exceeded:
                session["pending_entry"] = {
                    "date": date,
                    "weight": weight,
                    "body_fat": body_fat,
                    "visceral_fat": visceral_fat
                }
                session["previous_entry"] = {
                    "weight": prev_weight,
                    "body_fat": prev_body_fat,
                    "visceral_fat": prev_visc_fat
                }
                session["change_flags"] = thresholds_exceeded
                return redirect("/confirm_change")

        c.execute("""
            INSERT INTO body_metrics (date, weight, body_fat, visceral_fat)
            VALUES (?, ?, ?, ?)
        """, (date, weight, body_fat, visceral_fat))
        conn.commit()
        conn.close()

        return redirect("/log/metrics")  # or /log/meals
    return render_template("log_metrics.html")

@app.route("/confirm_overwrite", methods=["GET", "POST"])
def confirm_overwrite():
    if request.method == "POST":
        if request.form["action"] == "Replace":
            entry = session.pop("pending_entry")
            conn = sqlite3.connect("data/diet_tracker.db")
            c = conn.cursor()
            c.execute("""
                UPDATE body_metrics
                SET weight = ?, body_fat = ?, visceral_fat = ?
                WHERE date = ?
            """, (entry["weight"], entry["body_fat"], entry["visceral_fat"], entry["date"]))
            conn.commit()
            conn.close()
            if "pending_entry" in session:
                flash("✅ Entry replaced for " + entry["date"])
        else:
            if request.form["action"] == "Cancel":
                if "pending_entry" in session:
                    session.pop("pending_entry", None)
                    flash("❌ Entry canceled")
                session.pop("existing_entry", None)
        return redirect("/")
    return render_template("confirm_overwrite.html",
        entry=session.get("pending_entry"),
        existing=session.get("existing_entry")
    )

@app.route("/confirm_change", methods=["GET", "POST"])
def confirm_change():
    if request.method == "POST":
        if request.form["action"] == "Confirm":
            entry = session.pop("pending_entry")
            conn = sqlite3.connect("data/diet_tracker.db")
            c = conn.cursor()
            c.execute("""
                INSERT INTO body_metrics (date, weight, body_fat, visceral_fat)
                VALUES (?, ?, ?, ?)
            """, (entry["date"], entry["weight"], entry["body_fat"], entry["visceral_fat"]))
            conn.commit()
            conn.close()
            flash("✅ Entry added for " + entry["date"])
        else:
            flash("❌ Entry canceled")
        session.pop("previous_entry", None)
        session.pop("change_flags", None)
        return redirect("/log/metrics")
    return render_template("confirm_change.html",
        entry=session.get("pending_entry"),
        previous=session.get("previous_entry"),
        flags=session.get("change_flags")
    )

@app.route("/charts")
def charts():
    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()
    c.execute("""
        SELECT date, weight, body_fat, visceral_fat
        FROM body_metrics
        WHERE date >= DATE('now', '-90 days')
        ORDER BY date ASC
    """)
    rows = c.fetchall()
    conn.close()

    dates = [r[0] for r in rows]
    weights = [r[1] for r in rows]
    body_fats = [r[2] for r in rows]
    visceral_fats = [r[3] for r in rows]

    return render_template("charts.html",
        dates=json.dumps(dates),
        weights=json.dumps(weights),
        body_fats=json.dumps(body_fats),
        visceral_fats=json.dumps(visceral_fats)
    )

@app.route("/log/ingredient", methods=["GET", "POST"])
def log_ingredient():
    if request.method == "POST":
        data = (
            request.form["name"],
            request.form["quantity"],
            request.form["unit"],
            request.form["calories"],
            request.form["protein_g"],
            request.form["fiber_g"],
            request.form.get("fat_g"),
            request.form.get("carbs_g"),
            request.form.get("notes")
        )
        conn = sqlite3.connect("data/diet_tracker.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO ingredients (name, quantity, unit, calories, protein_g, fiber_g, fat_g, carbs_g, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()
        return redirect("/log/ingredient")
    return render_template("log_ingredient.html")

@app.route("/log/recipe", methods=["GET", "POST"])
def log_recipe():
    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()
    c.execute("SELECT id, name, quantity, unit FROM ingredients ORDER BY name")
    ingredients = c.fetchall()

    if request.method == "POST":
        name = request.form["name"]
        notes = request.form.get("notes")

        # Insert recipe
        c.execute("INSERT INTO recipes (name, notes) VALUES (?, ?)", (name, notes))
        recipe_id = c.lastrowid

        # Insert recipe items
        for key in request.form:
            if key.startswith("ingredient_"):
                ing_id = int(key.split("_")[1])
                amount = request.form[key]
                if amount:
                    c.execute("""
                        INSERT INTO recipe_items (recipe_id, ingredient_id, amount)
                        VALUES (?, ?, ?)
                    """, (recipe_id, ing_id, float(amount)))

        conn.commit()
        conn.close()
        flash(f"✅ Recipe '{name}' saved")
        return redirect("/log/recipe")

    conn.close()
    return render_template("log_recipe.html", ingredients=ingredients)

@app.route("/log/daily_menu", methods=["GET", "POST"])
def log_daily_menu():
    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()

    # Get recipes and ingredients
    c.execute("SELECT id, name FROM recipes ORDER BY name")
    recipes = c.fetchall()

    c.execute("SELECT id, name, quantity, unit FROM ingredients ORDER BY name")
    ingredients = c.fetchall()

    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        notes = request.form.get("notes")

        # Insert menu
        c.execute("INSERT INTO menus (name, date, notes) VALUES (?, ?, ?)", (name, date, notes))
        menu_id = c.lastrowid

        # Add selected recipes
        for key in request.form:
            if key.startswith("recipe_"):
                recipe_id = int(key.split("_")[1])
                portion_str = request.form[key]
                if portion_str.strip():  # skip empty or whitespace-only
                    portion = float(portion_str)
                    if portion > 0:
                        c.execute("INSERT INTO menu_recipes (menu_id, recipe_id, portion) VALUES (?, ?, ?)",
                                (menu_id, recipe_id, portion))

        # Add selected ingredients
        for key in request.form:
            if key.startswith("ingredient_"):
                ing_id = int(key.split("_")[1])
                amount_str = request.form[key]
                if amount_str.strip():
                    amount = float(amount_str)
                    c.execute("INSERT INTO menu_items (menu_id, ingredient_id, amount) VALUES (?, ?, ?)",
                            (menu_id, ing_id, amount))

        conn.commit()
        conn.close()
        flash(f"✅ Menu '{name}' saved for {date}")
        return redirect("/log/daily_menu")

    conn.close()
    return render_template("log_daily_menu.html", recipes=recipes, ingredients=ingredients)

# get the daily totals from start to end date
def get_daily_nutrition(c, start_date, end_date):
    c.execute("""
        WITH RECURSIVE date_range(date) AS (
            SELECT DATE(?)
            UNION ALL
            SELECT DATE(date, '+1 day')
            FROM date_range
            WHERE date < DATE(?)
        ),
        recipe_nutrition AS (
            SELECT m.date,
                   SUM((ri.amount * mr.portion / i.quantity) * i.calories) AS calories,
                   SUM((ri.amount * mr.portion / i.quantity) * i.carbs_g) AS carbs,
                   SUM((ri.amount * mr.portion / i.quantity) * i.protein_g) AS protein,
                   SUM((ri.amount * mr.portion / i.quantity) * i.fiber_g) AS fiber,
                   SUM((ri.amount * mr.portion / i.quantity) * i.fat_g) AS fat
            FROM menus m
            JOIN menu_recipes mr ON m.id = mr.menu_id
            JOIN recipe_items ri ON mr.recipe_id = ri.recipe_id
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE m.date BETWEEN DATE(?) AND DATE(?)
            GROUP BY m.date
        ),
        item_nutrition AS (
            SELECT m.date,
                   SUM((mi.amount / i.quantity) * i.calories) AS calories,
                   SUM((mi.amount / i.quantity) * i.carbs_g) AS carbs,
                   SUM((mi.amount / i.quantity) * i.protein_g) AS protein,
                   SUM((mi.amount / i.quantity) * i.fiber_g) AS fiber,
                   SUM((mi.amount / i.quantity) * i.fat_g) AS fat
            FROM menus m
            JOIN menu_items mi ON m.id = mi.menu_id
            JOIN ingredients i ON mi.ingredient_id = i.id
            WHERE m.date BETWEEN DATE(?) AND DATE(?)
            GROUP BY m.date
        )
        SELECT
            d.date,
            COALESCE(rn.calories, 0) + COALESCE(inu.calories, 0) AS total_calories,
            COALESCE(rn.carbs, 0) + COALESCE(inu.carbs, 0) AS total_carbs,
            COALESCE(rn.protein, 0) + COALESCE(inu.protein, 0) AS total_protein,
            COALESCE(rn.fiber, 0) + COALESCE(inu.fiber, 0) AS total_fiber,
            COALESCE(rn.fat, 0) + COALESCE(inu.fat, 0) AS total_fat
        FROM date_range d
        LEFT JOIN recipe_nutrition rn ON d.date = rn.date
        LEFT JOIN item_nutrition inu ON d.date = inu.date;
    """, (start_date, end_date, start_date, end_date, start_date, end_date))
    return c.fetchall()

@app.route("/view/menu/<int:menu_id>")
def view_menu(menu_id):
    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()
    
    # Get menu info
    c.execute("SELECT name, date, notes FROM menus WHERE id = ?", (menu_id,))
    menu = c.fetchone()

    # Get recipes in menu
    c.execute("""
        SELECT r.name, mr.portion, ri.ingredient_id, ri.amount, i.name, 
              i.calories, i.protein_g, i.carbs_g, i.fiber_g, i.fat_g, i.quantity
        FROM menu_recipes mr
        JOIN recipes r ON mr.recipe_id = r.id
        JOIN recipe_items ri ON ri.recipe_id = r.id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE mr.menu_id = ?
    """, (menu_id,))
    recipe_items = c.fetchall()

    # Get standalone ingredients
    c.execute("""
        SELECT i.name, mi.amount, i.calories, i.protein_g, i.carbs_g, i.fiber_g, i.fat_g, i.quantity
        FROM menu_items mi
        JOIN ingredients i ON mi.ingredient_id = i.id
        WHERE mi.menu_id = ?
    """, (menu_id,))
    direct_items = c.fetchall()

    # Nutrition totals
    c.execute("SELECT name, date, notes FROM menus WHERE id = ?", (menu_id,))
    menu = c.fetchone()

    today = menu[1]
    daily_data = get_daily_nutrition(c, today, today)
    #print(daily_data)

    conn.close()

    # Nutrition totals
    row = daily_data[0]  # ('2025-10-21', calories, carbs, protein, fiber, fat)

    # calculate macro percentages
    per_prot = round((100*row[3] * 4) / row[1], 1) if row[1] else 0
    per_carb = round((100*row[2] * 4) / row[1], 1) if row[1] else 0
    per_fat  = round((100*row[5] * 9) / row[1], 1) if row[1] else 0

    totals = {"calories": row[1], 
              "carbs": row[2], 
              "protein": row[3],
               "fiber": row[4], 
               "fat": row[5],
               "pct_carb":per_carb,
               "pct_prot":per_prot,
               "pct_fat":per_fat }

    return render_template("view_menu.html", menu=menu, recipe_items=recipe_items, direct_items=direct_items, totals=totals)

@app.route("/edit/menu/<int:menu_id>", methods=["GET", "POST"])
def edit_menu(menu_id):
    conn = sqlite3.connect("data/diet_tracker.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == "POST":
        # Update menu metadata
        name = request.form["name"]
        date = request.form["date"]
        notes = request.form["notes"]
        c.execute("UPDATE menus SET name = ?, date = ?, notes = ? WHERE id = ?", (name, date, notes, menu_id))

        # Clear old entries
        c.execute("DELETE FROM menu_recipes WHERE menu_id = ?", (menu_id,))
        c.execute("DELETE FROM menu_items WHERE menu_id = ?", (menu_id,))

        # Re-insert updated recipes
        c.execute("SELECT id FROM recipes")
        for row in c.fetchall():
            recipe_id = row["id"]
            key = f"recipe_{recipe_id}"
            portion_str = request.form.get(key, "").strip()
            if portion_str:
                portion = float(portion_str)
                if portion > 0:
                    c.execute("INSERT INTO menu_recipes (menu_id, recipe_id, portion) VALUES (?, ?, ?)",
                              (menu_id, recipe_id, portion))

        # Re-insert updated ingredients
        c.execute("SELECT id FROM ingredients")
        for row in c.fetchall():
            ing_id = row["id"]
            key = f"ingredient_{ing_id}"
            amount_str = request.form.get(key, "").strip()
            if amount_str:
                amount = float(amount_str)
                c.execute("INSERT INTO menu_items (menu_id, ingredient_id, amount) VALUES (?, ?, ?)",
                          (menu_id, ing_id, amount))

        conn.commit()
        conn.close()
        flash("✅ Menu updated successfully.")
        return redirect(f"/view/menu/{menu_id}")

    # GET: Load menu and prefill form
    c.execute("SELECT name, date, notes FROM menus WHERE id = ?", (menu_id,))
    menu = c.fetchone()

    c.execute("SELECT id, name FROM recipes ORDER BY name")
    recipes = c.fetchall()

    c.execute("SELECT id, name FROM ingredients ORDER BY name")
    ingredients = c.fetchall()

    # Get existing portions
    c.execute("SELECT recipe_id, portion FROM menu_recipes WHERE menu_id = ?", (menu_id,))
    recipe_portions = {row["recipe_id"]: row["portion"] for row in c.fetchall()}

    c.execute("SELECT ingredient_id, amount FROM menu_items WHERE menu_id = ?", (menu_id,))
    ingredient_amounts = {row["ingredient_id"]: row["amount"] for row in c.fetchall()}

    conn.close()
    return render_template("edit_menu.html", menu=menu, recipes=recipes, ingredients=ingredients,
                           recipe_portions=recipe_portions, ingredient_amounts=ingredient_amounts)

@app.route("/delete/menu/<int:menu_id>", methods=["POST"])
def delete_menu(menu_id):
    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()

    # Delete linked entries first
    c.execute("DELETE FROM menu_recipes WHERE menu_id = ?", (menu_id,))
    c.execute("DELETE FROM menu_items WHERE menu_id = ?", (menu_id,))
    c.execute("DELETE FROM menus WHERE id = ?", (menu_id,))

    conn.commit()
    conn.close()
    flash("🗑️ Menu deleted successfully.")
    return redirect("/")

def limit_flag(value, min_limit, max_limit):
    print(f"viceral {value}")
    if value is None:
        return ""
    if value < min_limit:
        return "✅"
    elif value > max_limit:
        return "❌"
    else:
        return "🟡"  # or "❕"

def arrow(new, old):
    if new is None or old is None:
        return ""
    if new > old:
        return "🔼"
    elif new < old:
        return "🔽"
    else:
        return "➖"

@app.route("/")
def home():
    conn = sqlite3.connect("data/diet_tracker.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # items for macronutrient summary
    c.execute("SELECT id, name, date FROM menus ORDER BY date DESC")
    menus = c.fetchall()

    # Latest 7 days
    c.execute("""
        SELECT AVG(weight), AVG(body_fat), AVG(visceral_fat)
        FROM body_metrics
        WHERE date >= DATE('now', '-7 days')
    """)
    latest = c.fetchone()

    # Previous 7 days
    c.execute("""
        SELECT AVG(weight), AVG(body_fat), AVG(visceral_fat)
        FROM body_metrics
        WHERE date >= DATE('now', '-14 days') AND date < DATE('now', '-7 days')
    """)
    previous = c.fetchone()

    conn = sqlite3.connect("data/diet_tracker.db")
    c = conn.cursor()
    
    end = date.today()
    start = end - timedelta(days=6)
    week_data = get_daily_nutrition(c, start.isoformat(), end.isoformat())
    '''print(f"today? {end}")
    for row in week_data:
        print(row)'''
    avg_calories = round(sum(row[1] for row in week_data) / len(week_data), 0)
    avg_carbs = round(sum(row[2] for row in week_data) / len(week_data), 0)
    avg_prot = round(sum(row[3] for row in week_data) / len(week_data), 0)
    avg_fiber = round(sum(row[4] for row in week_data) / len(week_data), 0)
    avg_fat = round(sum(row[5] for row in week_data) / len(week_data), 0)
    #print(avg_calories, avg_prot)

    end = date.today() - timedelta(days=7)
    start = end - timedelta(days=6)
    prev_data = get_daily_nutrition(c, start.isoformat(), end.isoformat())
    avg_calories_prev = round(sum(row[1] for row in prev_data) / len(prev_data), 0)
    avg_carbs_prev = round(sum(row[2] for row in prev_data) / len(prev_data), 0)
    avg_prot_prev = round(sum(row[3] for row in prev_data) / len(prev_data), 0)
    avg_fiber_prev = round(sum(row[4] for row in prev_data) / len(prev_data), 0)
    avg_fat_prev = round(sum(row[5] for row in prev_data) / len(prev_data), 0)
    conn.close()

    # calculate macro percentages
    per_prot = (avg_prot  * 4) / avg_calories if avg_calories else 0
    per_carb = (avg_carbs * 4) / avg_calories if avg_calories else 0
    per_fat  = (avg_fat   * 9) / avg_calories if avg_calories else 0

    # Nutrition totals
    totals = {"calories": avg_calories, 
              "carbs": avg_carbs, 
              "protein": avg_prot,
               "fiber": avg_fiber, 
               "fat": avg_fat,
               "prot_per":per_prot,
               "carb_per":per_carb,
               "fat_per":per_fat  }
    print(totals)

    return render_template("summary.html",
        menus=menus,
        avg_weight=round(latest[0], 1) if latest[0] else "—",
        weight_arrow=arrow(latest[0], previous[0]),
        avg_body_fat=round(latest[1], 1) if latest[1] else "—",
        body_fat_arrow=arrow(latest[1], previous[1]),
        body_fat_flag=limit_flag(latest[1], 25, 30),
        avg_visceral_fat=round(latest[2], 1) if latest[2] else "—",
        visceral_fat_arrow=arrow(latest[2], previous[2]),
        visceral_fat_flag=limit_flag(latest[2], 10, 14),
        avg_calories=avg_calories,
        calories_arrow=arrow(avg_calories, avg_calories_prev),
        avg_carbs=avg_carbs,
        carbs_arrow=arrow(avg_carbs_prev, avg_carbs_prev),
        avg_protein=avg_prot,
        protein_arrow=arrow(avg_prot, avg_prot_prev),
        avg_fiber=avg_fiber,
        fiber_arrow=arrow(avg_fiber, avg_fiber_prev),
        avg_fat=avg_fat,
        fat_arrow=arrow(avg_fat, avg_fat_prev),
        pct_protein=round(per_prot*100, 1),
        pct_carbs=round(per_carb*100, 1),
        pct_fat=round(per_fat*100, 1)
    )

if __name__ == "__main__":
    app.run(debug=True)