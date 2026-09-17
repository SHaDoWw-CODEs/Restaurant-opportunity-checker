"""
Step 2 (v3): Pull restaurant/cafe data for Greater Noida using the
CURRENT Foursquare Places API (places-api.foursquare.com).

WHY this version:
- Old v3 API and category IDs are dead (sunset May 2026) -- using new
  endpoint, Bearer auth, and required version header.
- Requesting 'rating' field explicitly to test if it's available on
  the free tier.
- Filtering food-related places by category name text (more robust
  than exact category ID matching, which keeps changing).
- Handles rate limiting (429 errors) with a retry + slower pacing.
"""

import requests
import pandas as pd
import time
import json

import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FOURSQUARE_API_KEY")

BASE_URL = "https://places-api.foursquare.com/places/search"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "X-Places-Api-Version": "2025-06-17"
}

# Greater Noida bounding box (south, west, north, east)
LAT_MIN, LON_MIN, LAT_MAX, LON_MAX = 28.40, 77.40, 28.55, 77.55
STEP = 0.008
RADIUS_METERS = 1000

FOOD_KEYWORDS = ["restaurant", "cafe", "coffee", "food", "diner", "eatery",
                  "bakery", "pizza", "burger", "bar", "pub", "dhaba"]

all_places = {}
lat = LAT_MIN
grid_points_queried = 0
debug_printed = False

while lat <= LAT_MAX:
    lon = LON_MIN
    while lon <= LON_MAX:
        params = {
            "ll": f"{lat},{lon}",
            "radius": RADIUS_METERS,
            "limit": 50,
            "fields": "fsq_place_id,name,latitude,longitude,categories"
        }
        try:
            resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
            if resp.status_code == 429:
                print(f"Rate limited at ({lat:.3f}, {lon:.3f}) - waiting 5s and retrying...")
                time.sleep(5)
                resp = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if not debug_printed and data.get("results"):
                print("\n--- DEBUG: sample raw place object ---")
                print(json.dumps(data["results"][0], indent=2)[:1500])
                print("--- END DEBUG ---\n")
                debug_printed = True

            for place in data.get("results", []):
                place_id = place.get("fsq_place_id") or place.get("fsq_id")
                if not place_id or place_id in all_places:
                    continue

                categories = place.get("categories", [])
                cat_text = " ".join(
                    c.get("name", "") if isinstance(c, dict) else str(c)
                    for c in categories
                ).lower()

                if any(kw in cat_text for kw in FOOD_KEYWORDS):
                    all_places[place_id] = place

            grid_points_queried += 1
            print(f"Queried ({lat:.3f}, {lon:.3f}) - food places so far: {len(all_places)}")
        except requests.exceptions.RequestException as e:
            print(f"Failed at ({lat:.3f}, {lon:.3f}): {e}")

        time.sleep(1.2)
        lon += STEP
    lat += STEP

print(f"\nFinished. Queried {grid_points_queried} grid points, found {len(all_places)} food places.")

rows = []
for place_id, place in all_places.items():
    categories = place.get("categories", [])
    cat_name = categories[0].get("name") if categories and isinstance(categories[0], dict) else "unspecified"
    rows.append({
        "place_id": place_id,
        "name": place.get("name", "Unknown"),
        "lat": place.get("latitude"),
        "lon": place.get("longitude"),
        "category": cat_name,
        "rating": place.get("rating"),
    })

df = pd.DataFrame(rows)
df.to_csv("greater_noida_restaurants_foursquare.csv", index=False)
print(df.head(10))
print(f"\nSaved {len(df)} rows to greater_noida_restaurants_foursquare.csv")
if len(df) > 0:
    print(f"Places with a rating: {df['rating'].notna().sum()} / {len(df)}")