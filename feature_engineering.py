import pandas as pd
from geopy.distance import geodesic

RADIUS_METERS = 500  # how far around a clicked point we look for competitors
PENALTY_PER_COMPETITOR = 8  # max points lost per competitor (at distance 0)


def load_restaurant_data(csv_path="greater_noida_restaurants_foursquare.csv"):
    """Load our pulled restaurant data."""
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["lat", "lon"])
    return df


def get_nearby_places(clicked_lat, clicked_lon, df, radius_m=RADIUS_METERS):
    """
    Given a clicked point, return all restaurants within radius_m meters,
    WITH their distance from the clicked point attached as a new column
    ("distance_m") so downstream scoring can use it.
    """
    clicked_point = (clicked_lat, clicked_lon)
    nearby = []
    for _, row in df.iterrows():
        place_point = (row["lat"], row["lon"])
        distance_m = geodesic(clicked_point, place_point).meters
        if distance_m <= radius_m:
            row_with_distance = row.copy()
            row_with_distance["distance_m"] = distance_m
            nearby.append(row_with_distance)

    if not nearby:
        empty_cols = list(df.columns) + ["distance_m"]
        return pd.DataFrame(columns=empty_cols)

    return pd.DataFrame(nearby)


def calculate_opportunity_score(nearby_df, radius_m=RADIUS_METERS):
    """
    Calculate a 0-100 opportunity score based on DISTANCE-WEIGHTED
    competitor density and category diversity.

    Formula (documented for your report):
    - Start at 100
    - For each nearby competitor, subtract:
          PENALTY_PER_COMPETITOR * (1 - distance_m / radius_m)
      So a competitor right on top of the clicked point costs the full
      8 points, while one near the edge of the radius costs close to 0.
    - If there are 3+ competitors but only 1 category type present,
      add a +10 "category gap" bonus (signals an underserved niche)
    - Clamp final score between 0 and 100
    """
    competitor_count = len(nearby_df)

    total_penalty = 0
    for _, row in nearby_df.iterrows():
        distance_weight = 1 - (row["distance_m"] / radius_m)
        total_penalty += PENALTY_PER_COMPETITOR * distance_weight

    score = 100 - total_penalty

    category_gap_bonus = 0
    if competitor_count >= 3:
        unique_categories = nearby_df["category"].nunique()
        if unique_categories == 1:
            category_gap_bonus = 10

    score += category_gap_bonus
    score = max(0, min(100, round(score)))

    return score, competitor_count, category_gap_bonus


def get_verdict_and_reason(clicked_lat, clicked_lon, df):
    """
    Main function: given a clicked point, return a verdict string and
    a short reason -- this is what the map popup will show.
    """
    nearby = get_nearby_places(clicked_lat, clicked_lon, df)
    score, competitor_count, gap_bonus = calculate_opportunity_score(nearby)

   
    if competitor_count == 0:
        verdict = "Insufficient Data"
        reason = ("No restaurants found in our dataset within 500m. "
                   "This could mean low competition OR simply that our "
                   "data doesn't cover this spot well -- verify manually "
                   "before relying on this result.")
        score = None
    elif score >= 70:
        verdict = "Good Opportunity"
    elif score >= 40:
        verdict = "Moderate Opportunity"
    else:
        verdict = "Risky - Saturated Area"

    if competitor_count > 0:
        category_counts = nearby["category"].value_counts().to_dict()
        top_categories = ", ".join(f"{cat} ({count})" for cat, count in list(category_counts.items())[:3])
        closest_distance = nearby["distance_m"].min()
        reason = (f"{competitor_count} competitor(s) within 500m "
                   f"(closest: {closest_distance:.0f}m). "
                   f"Categories: {top_categories}.")
        if gap_bonus > 0:
            reason += " Category gap detected -- possible niche opportunity."

    return {
        "score": score,
        "verdict": verdict,
        "reason": reason,
        "competitor_count": competitor_count
    }


if __name__ == "__main__":
    df = load_restaurant_data()
    print(f"Loaded {len(df)} restaurants.\n")

    test_points = [
        (28.4595, 77.5037, "Pari Chowk area"),
        (28.4744, 77.5044, "Knowledge Park area"),
        (28.4200, 77.4200, "Edge of bounding box - likely sparse"),
    ]

    for lat, lon, label in test_points:
        result = get_verdict_and_reason(lat, lon, df)
        print(f"--- {label} ({lat}, {lon}) ---")
        print(f"Score: {result['score']}  |  Verdict: {result['verdict']}")
        print(f"Reason: {result['reason']}\n")