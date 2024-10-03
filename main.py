# main.py
import asyncio
import json
from typing import List
from httpx import AsyncClient, Response
from urllib.parse import urlencode
from parsel import Selector
from parseProperties import parse_property, PropertyResult
import pandas as pd
import googlemaps
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

fileName = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
output_file = f"property_listings_{fileName}.xlsx"

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
gmaps = googlemaps.Client(key=api_key)

# 1. establish HTTP client with browser-like headers to avoid being blocked
client = AsyncClient(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,lt;q=0.8,et;q=0.7,de;q=0.6",
    },
    follow_redirects=True,
    http2=True,  # enable http2 to reduce block chance
    timeout=30,
)

async def find_locations(query: str) -> List[str]:
    """use rightmove's typeahead api to find location IDs. Returns list of location IDs in most likely order"""
    # rightmove uses two character long tokens so "marlow" becomes "CO/RN/WA/LL"
    tokenize_query = "".join(
        c + ("/" if i % 2 == 0 else "") for i, c in enumerate(query.upper(), start=1)
    )
    url = (
        f"https://www.rightmove.co.uk/typeAhead/uknostreet/{tokenize_query.strip('/')}/"
    )
    response = await client.get(url)
    data = json.loads(response.text)
    return [
        prediction["locationIdentifier"] for prediction in data["typeAheadLocations"]
    ]


async def scrape_search(location_id: str) -> dict:
    RESULTS_PER_PAGE = 24

    def make_url(offset: int) -> str:
        url = "https://www.rightmove.co.uk/api/_search?"
        params = {
            "areaSizeUnit": "sqft",
            "channel": "BUY",  # BUY or RENT
            "currencyCode": "GBP",
            "includeSSTC": "false",
            "index": offset,  # page offset
            "isFetching": "false",
            "locationIdentifier": location_id,  # e.g.: "REGION^61294",
            "numberOfPropertiesPerPage": RESULTS_PER_PAGE,
            "radius": "0.0",
            "sortType": "6",
            "viewType": "LIST",
        }
        return url + urlencode(params)

    first_page = await client.get(make_url(0))
    first_page_data = json.loads(first_page.content)
    total_results = int(first_page_data["resultCount"].replace(",", ""))
    results = first_page_data["properties"]

    other_pages = []
    # rightmove sets the API limit to 1000 properties
    max_api_results = 1000
    for offset in range(RESULTS_PER_PAGE, total_results, RESULTS_PER_PAGE):
        # stop scraping more pages when the scraper reach the API limit
        if offset >= max_api_results:
            break
        other_pages.append(client.get(make_url(offset)))
    for response in asyncio.as_completed(other_pages):
        response = await response
        data = json.loads(response.text)
        results.extend(data["properties"])
    return results


async def geocode_property(lat: float, lng: float) -> dict:
    """Use Google Geocoding API to get the exact address and split it into house number, street name, and post code."""
    geocode_result = gmaps.reverse_geocode((lat, lng))

    if geocode_result:
        address_components = geocode_result[0]["address_components"]
        house_number = ""
        street_name = ""
        post_code = ""

        # Loop through components and extract desired parts
        for component in address_components:
            if "street_number" in component["types"]:
                house_number = component["long_name"]
            if "route" in component["types"]:
                street_name = component["long_name"]
            if "postal_code" in component["types"]:
                post_code = component["long_name"]

        return {
            "house_number": house_number,
            "street_name": street_name,
            "post_code": post_code,
            "exact_address": geocode_result[0]["formatted_address"],
        }

    return {
        "house_number": "",
        "street_name": "",
        "post_code": "",
        "exact_address": "Address not found",
    }


async def geocode_properties(properties: List[PropertyResult]) -> List[PropertyResult]:
    """Geocode all properties concurrently and add house number, street name, post code, and exact address to property data."""
    
    async def geocode_and_update(property):
        lat = property["latitude"]
        lng = property["longitude"]
        geocoded_data = await geocode_property(lat, lng)

        # Add the new fields to the property data
        property["house_number"] = geocoded_data["house_number"]
        property["street_name"] = geocoded_data["street_name"]
        property["post_code"] = geocoded_data["post_code"]
        property["exact_address"] = geocoded_data["exact_address"]
        return property

    # Use asyncio.gather to run all geocoding operations concurrently
    updated_properties = await asyncio.gather(*[geocode_and_update(property) for property in properties])

    return updated_properties



async def runSearch():
    # Fetch results from scrape_search function
    # location_id = (await find_locations("marlow"))[0]
    marlow_results = await scrape_search("REGION^916")

    # Parse each result using the parse_property function
    parsed_results: List[PropertyResult] = [
        parse_property(property) for property in marlow_results
    ]

    # Geocode the first 5 properties
    updated_properties = await geocode_properties(parsed_results)

    # Convert the updated results into a pandas DataFrame
    df = pd.DataFrame(updated_properties)

    # Reorder the columns
    column_order = [
        "id",
        "house_number",
        "street_name",
        "post_code",
        "price",
        "branchDisplayName",
        "firstVisibleDate",
        "daysOnMarket",
        "propertyUrl",
        "contactUrl",
        "listingUpdateReason",
        "listingUpdateDate",
        "latitude",
        "longitude",
        "displayAddress",
        "exact_address",
    ]

    df["firstVisibleDate"] = pd.to_datetime(df["firstVisibleDate"], utc=True)  # Ensure it's in UTC

    # Calculate daysOnMarket
    df["daysOnMarket"] = (pd.Timestamp.now(tz='UTC') - df["firstVisibleDate"]).dt.days  # Ensure now() is also UTC

    # Convert firstVisibleDate to naive datetime (remove timezone)
    df["firstVisibleDate"] = df["firstVisibleDate"].dt.tz_localize(None)

    df["propertyUrl"] = "https://www.rightmove.co.uk" + df["propertyUrl"]
    df["contactUrl"] = "https://www.rightmove.co.uk" + df["contactUrl"]

    df = df[column_order]
    # Print the first few rows of the DataFrame
    print(len(df.index))
    print(df.head())
    df.to_excel(output_file, index=False, sheet_name="Property Listings")
    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(runSearch())
