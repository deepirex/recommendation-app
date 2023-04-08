from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pymongo
import certifi
from bson import json_util, ObjectId
from json import JSONEncoder
from urllib.parse import quote



class CustomJSONEncoder(JSONEncoder):
   def default(self, obj):
       if isinstance(obj, ObjectId):
           return str(obj)
       return super(CustomJSONEncoder, self).default(obj)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]


creds = ServiceAccountCredentials.from_json_keyfile_name("/Users/Deepak/Downloads/foodra-2ce6c11940ab.json", scope)
client_gs = gspread.authorize(creds)


sheet = client_gs.open_by_key("1-ALF3cj103Z6gOzyzmvNlVwj12hJ3w8Gxi3Bs3CzWQQ").sheet1


mongo_connection_string = "mongodb+srv://deepaks:mbuDF80kgmihCakR@cluster0.kwbheiu.mongodb.net/food_recommendation?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_connection_string, tlsCAFile=certifi.where())


db = client['food_recommendation']
recipes_collection = db['recipes']


@app.route('/')
def index():
   return render_template('index.html')


@app.route('/refresh_data', methods=['GET'])
def refresh_data():
   sheet = client_gs.open_by_key("1-ALF3cj103Z6gOzyzmvNlVwj12hJ3w8Gxi3Bs3CzWQQ").sheet1
   recipes_collection.delete_many({})
   load_data_to_mongodb(sheet, recipes_collection)
   return "Data refreshed"


from pymongo import ASCENDING

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    cuisine = request.form.getlist('cuisine')
    dietary_preference = request.form.get('dietary_preference')
    allergens = request.form.getlist('allergens[]')
    health_quotient = request.form.get('health_quotient')
    spiciness = request.form.get('spiciness')
    course = request.form.get('course')
    cooking_method = request.form.get('cooking_method')

    filter_criteria = {}

    if cuisine:
        filter_criteria['cuisine'] = {'$in': cuisine}
    if dietary_preference:
        filter_criteria['type'] = dietary_preference
    if allergens:
        filter_criteria['allergens'] = {'$nin': allergens}
    if health_quotient:
        filter_criteria['health_quotient'] = health_quotient
    if spiciness:
        filter_criteria['spiciness'] = spiciness
    if course:
        filter_criteria['course'] = course
    if cooking_method:
        filter_criteria['cooking_method'] = cooking_method

    if filter_criteria:
        pipeline = [{'$match': filter_criteria}, {'$sample': {'size': 7}}]
    else:
        pipeline = [{'$sample': {'size': 7}}]

    recommendations = list(recipes_collection.aggregate(pipeline))

    recommendations_data = []
    for r in recommendations:
        dish_name = r['title']
        delivery_app_url = f'https://www.swiggy.com/search?query={quote(dish_name)}'
        recipe_search_url = f'https://www.google.com/search?q={quote(dish_name + " recipe")}'
        recommendations_data.append({'dish_name': dish_name, 'delivery_app_url': delivery_app_url, 'recipe_search_url': recipe_search_url})

    return jsonify(recommendations_data)





def load_data_to_mongodb(sheet, recipes_collection):
    all_recipes = sheet.get_all_records()
    for recipe in all_recipes:
        transformed_recipe = {
            'title': recipe['Dish'],
            'cuisine': recipe['Cuisine'].split(', '),
            'type': recipe['Type'],
            'taste': recipe['Taste'],
            'meal_time': recipe['Meal Time'],
            'state': recipe['State'],
            'spiciness': recipe['Spiciness'],
            'cooking_method': recipe['Cooking method'],
            'oiliness': recipe['Oiliness'],
            'allergens': recipe['Allergens'].split(', '),
            'ingredients': recipe['Ingredients'],
            'serving_temperature': recipe['Serving Temperature'],
            'combo': recipe['Combo'],
            'health_quotient': recipe['health quotient'],
            'calories': recipe['calories'],
            'nutritional_benefits': recipe['Nutritional benefits'],
            'nutritional_values': recipe['Nutritional values'],
            'fiber_quotient': recipe['Fiber Quotient'],
            'description': recipe['Description/Write-up'],
            'course': recipe['Course'],  # Added the "Course" field
        }
        existing_recipe = recipes_collection.find_one({'title': transformed_recipe['title']})
        if not existing_recipe:
            recipes_collection.insert_one(transformed_recipe)




if __name__ == '__main__':
   app.run(debug=True)