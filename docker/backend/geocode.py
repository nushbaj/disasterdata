import pandas as pd
import requests
import sqlite3
import asyncio
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()
API_URL=os.getenv('API_URL')
if API_URL:
    print(f"API_URL loaded successfully: {API_URL}")
DB_FILE=os.getenv('DB_FILE')
if DB_FILE:
    print(f"DB_FILE loaded successfully: {DB_FILE}")
API_KEY=os.getenv('API_KEY')
if API_KEY:
    print(f"API_KEY loaded successfully: {API_KEY}")
geocode_url=os.getenv('geocode_url')
if geocode_url:
    print(f"geocode_url loaded successfully: {geocode_url}")
MAX_RPS=5 #maximum of 5 requests per second 


#fetching data from the database
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            if response.status != 200:
                return pd.DataFrame()
            else:
                data = await response.json()
                posts = data.get("posts", [])
                return pd.DataFrame(posts)
#create database table
def create_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        conn.execute('''CREATE TABLE IF NOT EXISTS locations(
        location_name TEXT PRIMARY KEY,
        latitude REAL,
        longitude REAL)''')

#checking whether the location is already cached
def check_db(location):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT latitude, longitude FROM locations WHERE location_name = ?", (location,))
        return cursor.fetchone()

#saving new coordinates into db
def save_in_db(location, latitude, longitude):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO locations (location_name, latitude, longitude) VALUES (?, ?, ?)", (location, latitude, longitude))
        conn.commit()

async def fetch_geocode(session, q, semaphore):
    #location skipped if in cache
    if check_db(location):  
        print(f"Cache hit: {location}")
        return None 
    
    #Only allowing 5 concurrent tasks
    async with semaphore:
        try:
            async with session.get(geocode_url.format(q, API_KEY)) as response: #q is location param
                if response.status == 200:
                    data = await response.json()
                else:
                    print(f"Failed to geocode location for {location} with Status Code: {response.status}")
                    return None
        except Exception as e:
            print(f"Error in retrieving coordinates for {location} with {e}")
            return None
    
    #matching the API response format
    if data.get("items"):  
        lat = data["items"][0]["position"]["lat"]
        lng = data["items"][0]["position"]["lng"]

        #save into database
        save_in_db(location, lat, lng)  
        print(f"Saved: {location} as ({lat}, {lng})")
        return (location, lat, lng)
    
    print(f"Failed to geocode: {location}")
    return None

async def geocode_locations(df):

    #respecting rate limit with semaphore
    semaphore = asyncio.Semaphore(MAX_RPS)  
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_geocode(session, loc, semaphore) for loc in df["location"]]

        #process results once complete
        for task in asyncio.as_completed(tasks):
            await task

async def main():
    print()
    df = await fetch_data()
    if df.empty:
        print("No data found")
    else:
        print(f"Data fetched successfully. Columns of original dataframe: {df.columns}")

        #Extracting only non-null, unique locations
        df_cleaned = df[['location']].dropna().drop_duplicates().reset_index(drop=True) 
        print(f"Cleaned Dataframe: \n{df_cleaned.head(5)}\nProcessing {df_cleaned.size} locations...")
        await geocode_locations(df_cleaned)

if __name__ == "__main__":
    asyncio.run(main())