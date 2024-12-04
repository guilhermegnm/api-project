from bs4 import BeautifulSoup
import requests
from lxml import etree
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mangum import Mangum # type: ignore

# 1.1. Auxiliar functions
def extract_source(url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'}
        source=requests.get(url, headers=headers).text
        return source

def extract_data(source):
    soup = BeautifulSoup(source)
    return soup

def safe_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error calling {func.__name__}: {e}")
        return None

# 2.1. Title
def get_title(soup):
    title_string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[1]/h1/span/text()[1]'
    title = etree.HTML(str(soup)).xpath(title_string)[0]
    return title

# 2.2. Price & weight
def get_price(soup):
    price_string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/span/text()[1]'
    price_kg_string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[1]/div/span/text()[6]'

    price_dict = {
        "price_euro": float(''.join(value for value in etree.HTML(str(soup)).xpath(price_string))),
        "price_euro_kg": float(etree.HTML(str(soup)).xpath(price_kg_string)[0].replace(",", "."))
    }

    return price_dict

def get_weight(soup):
    weight_string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[1]/div/text()[1]'
    weight = etree.HTML(str(soup)).xpath(weight_string)[0]
    return weight


# 2.3. Intro description block
def get_expire(soup):
    string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[3]/div/div/span'
    element = etree.HTML(str(soup)).xpath(string)[0]
    return ''.join(element.itertext()).strip()

def get_nutriscore(soup):
    string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[4]/div[1]/svg/title/text()'
    return etree.HTML(str(soup)).xpath(string)[0]

def get_intro_desc_text(soup):
    string = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[4]/div[2]/p/text()'
    return etree.HTML(str(soup)).xpath(string)[0]

def get_intro_desc_i(soup):

    prefix = '//*[@id="start-of-content"]/div[1]/div/div/div/article/div/div/div[2]/div[4]/div[2]/ul'

    # Dynamically adjust table size
    prefix_size = len(etree.HTML(str(soup)).xpath(prefix)[0])

    return [etree.HTML(str(soup)).xpath(f'{prefix}/li[{i+1}]/text()')[0] for i in range(prefix_size)]

def get_intro_desc(soup):
    return {
        "intro_desc_text": get_intro_desc_text(soup),
        "intro_desc_b_pts": get_intro_desc_i(soup),
    }

# 2.4. Main description block
def get_main_desc_i(soup):

    prefix = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[1]/div[1]/ul'

    # Dynamically adjust table size
    prefix_size = len(etree.HTML(str(soup)).xpath(prefix)[0])

    return [etree.HTML(str(soup)).xpath(f'{prefix}/li[{i+1}]/text()')[0] for i in range(prefix_size)]

# 2.5. Miscellaneous information
def get_servings(soup):
    servings_size = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[1]/div[2]/dl/span[1]/dd/text()'
    servings_amount = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[1]/div[2]/dl/span[2]/dd/text()'

    servings_dict = {
        "servings_size": etree.HTML(str(soup)).xpath(servings_size)[0],
        "servings_amount": etree.HTML(str(soup)).xpath(servings_amount)[0]}
    return servings_dict

def get_climate(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[1]/div[2]/p[2]'
    element = etree.HTML(str(soup)).xpath(string)[0]
    return ''.join(element.itertext()).strip()

def get_alergens(soup):

    prefix = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[1]/ul'

    # Dynamically adjust table size
    prefix_size = len(etree.HTML(str(soup)).xpath(prefix)[0])

    alergens_list = [etree.HTML(str(soup)).xpath(f'{prefix}/li[{i+1}]/p/text()')[0] for i in range(prefix_size)]

    return alergens_list

# 2.6. Ingredients
def get_ingredients(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[2]/p/span'
    element = etree.HTML(str(soup)).xpath(string)[0]
    return ' '.join(element.itertext()).strip()

# 2.7. Nutrition
def get_nutrition(soup):

    nutrition_table_string_prefix = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[3]/table/tbody/'
    # Dynamically adjust nutrition table size
    nutrition_table_size = len(etree.HTML(str(soup)).xpath('//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/div[3]/table/tbody')[0])

    nutrition_dict = {etree.HTML(str(soup)).xpath(f'{nutrition_table_string_prefix}tr[{i+1}]/td[1]')[0].text: etree.HTML(str(soup)).xpath(f'{nutrition_table_string_prefix}tr[{i+1}]/td[2]')[0].text for i in range(nutrition_table_size)}

    return nutrition_dict


# 2.8. Dropdown blocks
def get_advice_use(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/fieldset[1]/main/div/div/dl/span/dd/text()'
    return etree.HTML(str(soup)).xpath(string)[0]
def get_advice_keep(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/fieldset[2]/main/div/p/span//text()'
    return etree.HTML(str(soup)).xpath(string)
def get_advice_origin(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/fieldset[3]/main/div/div/p/span//text()'
    return etree.HTML(str(soup)).xpath(string)
def get_advice_contact(soup):
    string = '//*[@id="start-of-content"]/div[2]/div/div[1]/div[1]/fieldset[4]/main/div/div/address/div//text()'
    return etree.HTML(str(soup)).xpath(string)


# 3.1. Wrap up everything
def get_item(url):

    soup = extract_data(extract_source(url))

    # Dynamically build the dictionary
    item_dict = {
        key: value
        for key, value in {
            # 1. Title
            "title": safe_call(get_title, soup),
            # 2. Price & weight
            "price": safe_call(get_price, soup),
            "weight": safe_call(get_weight, soup),
            # 3. Intro description block
            "expiration": safe_call(get_expire, soup),
            "nutriscore": safe_call(get_nutriscore, soup),
            "intro_desc": safe_call(get_intro_desc, soup),
            # 4. Main description block
            "main_desc": safe_call(get_main_desc_i, soup),
            # 5. Miscellaneous information
            "servings" : safe_call(get_servings, soup),
            "climate" : safe_call(get_climate, soup),
            "alergens": safe_call(get_alergens, soup),
            # 6. Ingredients
            "ingredients": safe_call(get_ingredients, soup),
            # 7. Nutrition
            "nutrition": safe_call(get_nutrition, soup),
            # 8. Dropdown blocks
            "use": safe_call(get_advice_use, soup),
            "keep": safe_call(get_advice_keep, soup),
            "origin": safe_call(get_advice_origin, soup),
            "contact": safe_call(get_advice_contact, soup),
        }.items() if value is not None}

    return item_dict

# 4.1. Build API

# Create a FastAPI instance
app = FastAPI()

# Define a Pydantic model for the input
class URLRequest(BaseModel):
    url: str

# Define an API endpoint
@app.post("/")
def process_url_endpoint(request: URLRequest):
    try:
        # Call your existing function
        result = get_item(request.url)
        return {"success": True, "data": result}
    except Exception as e:
        logging.error(f"Error processing URL: {str(e)}")
        raise HTTPException(status_code=500, detail="deu erro")

# %%
handler = Mangum(app)