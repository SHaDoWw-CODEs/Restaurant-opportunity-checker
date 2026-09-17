# Restaurant Location Opportunity Checker

An interactive tool to check how promising a location in Greater Noida is for opening a new restaurant, based on nearby competitor density and category diversity.

Built as a Data Visualization & Analysis course project (Second Year, B.Tech CSE - AIML).

## What it does

Click any point on the map within Greater Noida, and the app calculates an **Opportunity Score (0-100)** based on:
- How many restaurants already exist nearby (within 500m)
- How close those competitors are (closer competitors count more, via distance-weighting)
- Whether there's a category gap (e.g. many restaurants nearby but no cafes)

The verdict is shown both as a colored marker on the map and as a detailed breakdown in the sidebar, including a table of nearby competitors.

## Why no star ratings?

Both Google Places API (requires prepayment) and Foursquare Places API (ratings are a Premium-only field) gate review/rating data behind paid tiers. Instead of faking this signal, this project deliberately focuses on **market saturation** as an honest, freely-available proxy for opportunity -- arguably a more directly useful signal for a "should I open here" decision than star ratings anyway.

## Tech Stack

- **Data source:** Foursquare Places API (current `places-api.foursquare.com` endpoint)
- **Distance calculations:** geopy (geodesic distance)
- **Interactive map:** Folium + streamlit-folium
- **UI:** Streamlit
- **Data handling:** pandas

## Setup

1. Clone this repo
2. Install dependencies:
   ```
   pip install requests pandas folium streamlit streamlit-folium geopy python-dotenv
   ```
3. Create a `.env` file in the project root with your own Foursquare API key:
   ```
   FOURSQUARE_API_KEY=your_key_here
   ```
   (Get a free key at [foursquare.com/developers](https://foursquare.com/developers))
4. (Optional) Re-pull fresh data:
   ```
   python fetch_restaurants_foursquare_v3.py
   ```
5. Run the app:
   ```
   python -m streamlit run app.py
   ```

## Project Structure

```
├── app.py                              # Main Streamlit app
├── feature_engineering.py              # Opportunity scoring logic
├── fetch_restaurants_foursquare_v3.py  # Data collection script
├── greater_noida_restaurants_foursquare.csv  # Collected dataset (108 places)
├── .env                                # API key (not committed)
└── .gitignore
```

## Known Limitations

- **Dataset size:** 108 restaurants across Greater Noida is not exhaustive. Sparse areas may show "Insufficient Data" even if they're genuinely viable locations -- this is a data coverage limitation, not a claim about the location itself.
- **No review/rating signal:** Both major providers gate this behind paid tiers, so the score reflects market saturation only, not customer sentiment.
- **Proxy label:** There is no public ground-truth "this restaurant succeeded/failed" dataset, so the scoring formula is a reasoned heuristic (documented in `feature_engineering.py`), not a trained/validated predictive model.
- Always verify with on-ground research before making real business decisions based on this tool.

## Development Notes

This project involved a real mid-development pivot: Foursquare's legacy v3 Places API was sunset in May 2026, requiring a switch to their new endpoint, auth format, and category system mid-project. The `rating` field also turned out to be Premium-gated, which led to the decision to focus on market saturation instead of review scores -- a good example of adapting scope to real-world data constraints rather than the difficulty being a project flaw.