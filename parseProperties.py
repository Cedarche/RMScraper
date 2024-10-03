from typing import TypedDict
import jmespath


class PropertyResult(TypedDict):
    """this is what our result dataset will look like"""

    id: str
    phone: str
    bedrooms: int
    bathrooms: int
    displayAddress: str
    latitude: float
    longitude: float
    property_type: str
    summary: str
    price: str
    size: str
    propertyUrl: str
    contactUrl: str
    firstVisibleDate: str
    addedOrReduced: str
    listingUpdateReason: str
    listingUpdateDate: str
    branchDisplayName: str


def parse_property(data) -> PropertyResult:
    """parse rightmove cache data for proprety information"""
    # here we define field name to JMESPath mapping
    parse_map = {
        "id": "id",
        "phone": "customer.contactTelephone",
        "bedrooms": "bedrooms",
        "bathrooms": "bathrooms",
        "displayAddress": "displayAddress",
        "latitude": "location.latitude",
        "longitude": "location.longitude",
        "property_type": "propertySubType",
        "summary": "summary",
        "price": "price.amount",
        "size": "displaySize",
        "propertyUrl": "propertyUrl",
        "contactUrl": "contactUrl",
        "firstVisibleDate": "firstVisibleDate",
        "addedOrReduced": "addedOrReduced",
        "listingUpdateReason": "listingUpdate.listingUpdateReason",
        "listingUpdateDate": "listingUpdate.listingUpdateDate",
        "branchDisplayName": "customer.branchDisplayName",
    }

    results = {}
    for key, path in parse_map.items():
        value = jmespath.search(path, data)
        results[key] = value
    return results
