import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import requests
import json

# Streamlit page configuration
st.set_page_config(page_title="Interactive Recipe Journal", layout="wide")
st.title("🍽️ **Recipe Journal with Nutritional Tracking**")

# Connect to SQLite database
conn = sqlite3.connect("recipe_journal.db")
c = conn.cursor()

# Create database tables
c.execute('''
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_name TEXT,
    ingredients TEXT,
    steps TEXT,
    calories INTEGER,
    protein REAL,
    carbs REAL,
    fats REAL,
    created_on TEXT
)
''')
conn.commit()

# Edamam API credentials
APP_ID = "e91d0dfd"
API_KEY = "0beedbcb58d241bbd88d5ec5dcd63fe5"

# Function to fetch nutrition data from Edamam API
def get_nutrition_info(ingredients):
    url = f"https://api.edamam.com/api/nutrition-details?app_id={APP_ID}&app_key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "title": "Recipe",
        "ingr": ingredients.splitlines()  # Convert multiline input to list
    }
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        calories = data.get("calories", 0)
        protein = data.get("totalNutrients", {}).get("PROCNT", {}).get("quantity", 0)
        carbs = data.get("totalNutrients", {}).get("CHOCDF", {}).get("quantity", 0)
        fats = data.get("totalNutrients", {}).get("FAT", {}).get("quantity", 0)
        return calories, protein, carbs, fats
    else:
        st.error("Could not retrieve nutrition information.")
        return 0, 0, 0, 0

# Function to add a new recipe
def add_recipe(recipe_name, ingredients, steps, calories, protein, carbs, fats):
    created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
    INSERT INTO recipes (recipe_name, ingredients, steps, calories, protein, carbs, fats, created_on)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (recipe_name, ingredients, steps, calories, protein, carbs, fats, created_on))
    conn.commit()
    st.success(f"Recipe '{recipe_name}' added successfully!")

# Function to get all recipes
def get_all_recipes(sort_by=None):
    if sort_by == "name":
        c.execute("SELECT * FROM recipes ORDER BY recipe_name ASC")
    elif sort_by == "date":
        c.execute("SELECT * FROM recipes ORDER BY created_on DESC")
    elif sort_by == "calories":
        c.execute("SELECT * FROM recipes ORDER BY calories DESC")
    else:
        c.execute("SELECT * FROM recipes ORDER BY created_on DESC")
    return c.fetchall()

# Function to search recipes by name
def search_recipes(query):
    c.execute("SELECT * FROM recipes WHERE recipe_name LIKE ?", ('%' + query + '%',))
    return c.fetchall()

# Function to delete a recipe by ID
def delete_recipe(recipe_id):
    c.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()

# Function to update a recipe
def update_recipe(recipe_id, recipe_name, ingredients, steps, calories, protein, carbs, fats):
    c.execute('''
    UPDATE recipes
    SET recipe_name = ?, ingredients = ?, steps = ?, calories = ?, protein = ?, carbs = ?, fats = ?
    WHERE id = ?
    ''', (recipe_name, ingredients, steps, calories, protein, carbs, fats, recipe_id))
    conn.commit()
    st.success("Recipe updated successfully!")

# Sidebar actions
st.sidebar.title("Actions")
action = st.sidebar.radio("Select an action:", ["Add Recipe", "View Recipes", "Nutritional Summary"])

# Sidebar information about the app
with st.sidebar.expander("About the Journal"):
    st.write("""
        ## Recipe Journal with Nutritional Tracking
        This project is a digital recipe journal that lets users save, update, and search recipes while tracking their nutritional content.
    """)

# Layout for adding a recipe
if action == "Add Recipe":
    st.header("Add a New Recipe")
    col1, col2 = st.columns([3, 2])

    with col1:
        recipe_name = st.text_input("Recipe Name", placeholder="Enter the recipe name")
        ingredients = st.text_area("Ingredients", placeholder="List ingredients with quantities, e.g., '2 eggs, 1 cup flour'")
        steps = st.text_area("Steps", placeholder="Describe the preparation steps")

    if st.button("Fetch Nutrition Info"):
        if ingredients:
            calories, protein, carbs, fats = get_nutrition_info(ingredients)
            st.session_state['nutrition_info'] = (calories, protein, carbs, fats)
        else:
            st.error("Please enter ingredients to fetch nutrition information.")

    # Initialize or retrieve nutritional info
    if 'nutrition_info' in st.session_state:
        calories, protein, carbs, fats = st.session_state['nutrition_info']
    else:
        calories = 0
        protein = 0.0
        carbs = 0.0
        fats = 0.0

    with col2:
        st.subheader("Nutritional Information (per serving)")
        calories = st.number_input("Calories (kcal)", value=int(calories), min_value=0, step=10)
        protein = st.number_input("Protein (g)", value=float(protein), min_value=0.0, step=0.1)
        carbs = st.number_input("Carbs (g)", value=float(carbs), min_value=0.0, step=0.1)
        fats = st.number_input("Fats (g)", value=float(fats), min_value=0.0, step=0.1)
    
    if st.button("Add Recipe"):
        if recipe_name and ingredients and steps:
            add_recipe(recipe_name, ingredients, steps, calories, protein, carbs, fats)
            if 'nutrition_info' in st.session_state:
                del st.session_state['nutrition_info']  # Clear saved nutrition data after adding recipe
        else:
            st.error("Please fill in all fields to add a recipe.")

# Layout for viewing, sorting, and searching recipes
elif action == "View Recipes":
    st.header("All Recipes")

    # Search box
    search_query = st.text_input("Search Recipes by Name", "")
    sort_by = st.selectbox("Sort by", ["Date Added", "Name", "Calories"])
    
    if search_query:
        recipes = search_recipes(search_query)
    else:
        recipes = get_all_recipes(sort_by="name" if sort_by == "Name" else "date" if sort_by == "Date Added" else "calories")
    
    if recipes:
        for recipe in recipes:
            st.subheader(f"{recipe[1]}")
            st.write(f"**Ingredients**: {recipe[2]}")
            st.write(f"**Steps**: {recipe[3]}")
            st.write(f"**Calories**: {recipe[4]} kcal | **Protein**: {recipe[5]} g | **Carbs**: {recipe[6]} g | **Fats**: {recipe[7]} g")
            st.markdown(f"**Date Added**: {recipe[8]}")
            
            # Delete button with a unique key
            if st.button(f"Delete {recipe[1]}", key=f"delete_{recipe[0]}"):
                delete_recipe(recipe[0])
                st.rerun()  # Refresh the page after deletion
            
            # Edit button with a unique key
            if st.button(f"Edit {recipe[1]}", key=f"edit_{recipe[0]}"):
                recipe_name = st.text_input("Edit Recipe Name", value=recipe[1])
                ingredients = st.text_area("Edit Ingredients", value=recipe[2])
                steps = st.text_area("Edit Steps", value=recipe[3])
                calories = st.number_input("Edit Calories (kcal)", value=recipe[4], min_value=0)
                protein = st.number_input("Edit Protein (g)", value=recipe[5], min_value=0.0)
                carbs = st.number_input("Edit Carbs (g)", value=recipe[6], min_value=0.0)
                fats = st.number_input("Edit Fats (g)", value=recipe[7], min_value=0.0)

                if st.button("Save Changes", key=f"save_{recipe[0]}"):
                    update_recipe(recipe[0], recipe_name, ingredients, steps, calories, protein, carbs, fats)
                    st.rerun()  # Refresh the page after update
    else:
        st.write("No recipes found.")

# Nutritional Summary section
elif action == "Nutritional Summary":
    st.header("Nutritional Summary")

    # Fetch total values for calories, protein, carbs, and fats
    c.execute("SELECT SUM(calories), SUM(protein), SUM(carbs), SUM(fats) FROM recipes")
    summary = c.fetchone()

    if summary:
        st.write(f"**Total Calories**: {summary[0]} kcal")
        st.write(f"**Total Protein**: {summary[1]} g")
        st.write(f"**Total Carbs**: {summary[2]} g")
        st.write(f"**Total Fats**: {summary[3]} g")
    else:
        st.write("No data available.")

