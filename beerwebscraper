import requests
from bs4 import BeautifulSoup
import json

# Replace this URL with the actual forum URL
url = "https://www.example-homebrewing-forum.com/recipes"

# Send an HTTP request and parse the content with BeautifulSoup
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Function to extract recipe information from an individual post
def extract_recipe(post):
    recipe = {}
    try:
        recipe["title"] = post.find("div", class_="recipe-title").text.strip()
        recipe["author"] = post.find("div", class_="recipe-author").text.strip()
        recipe["date"] = post.find("div", class_="recipe-date").text.strip()
        recipe["ingredients"] = post.find("div", class_="recipe-ingredients").text.strip()
        recipe["instructions"] = post.find("div", class_="recipe-instructions").text.strip()
    except AttributeError:
        return None
    return recipe

# Find all the recipe posts on the page
recipe_posts = soup.find_all("div", class_="recipe-post")

# Extract the recipe data from each post
recipes = []
for post in recipe_posts:
    recipe = extract_recipe(post)
    if recipe:
        recipes.append(recipe)

# Save the recipes as a JSON file
with open("homebrew_recipes.json", "w") as f:
    json.dump(recipes, f, indent=2)

print("Downloaded {} recipes.".format(len(recipes)))
