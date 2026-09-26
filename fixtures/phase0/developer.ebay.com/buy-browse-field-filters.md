---
url: https://www.developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl, www host)
---

Buy API Field Filters | eBay Developers Program

 Buy API Field Filters

Developers Program

- 
Join

- Overview

- About the Program

- Benefits

- Policies

- API License Agreement

Develop


Get Started with APIs


- Authorization

- Using eBay RESTful APIs

- API Call Limits

- API Deprecations

- API Status

Selling Applications

- Listing Management

- Listing Metadata

- Account Management

- Order Management

- Offers and Leads

- Communication

- Marketing and Promotions

- Analytics and Reporting

- Other APIs

- App Settings & Insight

Buying Applications

- Inventory Discovery & Refresh

- Marketing and Discounts

- Marketplace Metadata

- Checkout/Bid




- All guides

- SDKs & Widgets

Tools


eBay Sandbox


- Create Test Users

- Reset Password

- Sandbox Status

- Sandbox Site

- API Explorer

- GraphQL Explorer

- WSDL Pruner

Grow


- Application Growth Check

- Affiliate Program

- Loyalty Program

- Events

- Awards

Updates


- API Updates

- Newsletter

- Blog

- Survey

Support



- FAQs

- Developer Community Forum

- Knowledge Base

- Developer Account Support

- Developer Technical Support

- Sign in

- Theme

- Join






- Develop


- Get Started with APIs







- Selling Applications











- Buying Applications










- Tools


- eBay Sandbox









- Grow







- Updates






- Support








HomeDevelopGuidesBuying Integration GuideBuy API Field Filters

# Buy API Field Filters

Buying Integration Guide 

Buy APIs Overview

Buy APIs Requirements

Browse API

Charity API

Deal API

Feed API

Feed API beta

Marketing API

Marketplace Insights API

Offer API

Order API

Categories for Buy APIs

Buy API Support by Marketplace


The following table contains the details of the field filters supported in the Buy APIs. You use these filters to control the items returned in the response. You can use more that one filter in a method.
Not all of these filters are supported by all Buy API methods. The API/Method column shows you which Buy API methods support that filter.

Note: 
 Query parameter values need to be URL encoded. For details, see URL encoding query parameter values. For readability, code examples in this document have not been URL encoded.

Note: The Marketplace Insights API is restricted and not open to new users at this time. 

Filter name

API/Method

Syntax

Description

bidCount

Browse:
- search

- searchByImage

filter=bidCount:[1..5]

Only items with a number of bids within the specified range are returned.

The first value is the lower number of bids and the second value is the higher number of bids. The lower and higher values are separated by two dots ('..'). In the syntax example provided, only items with 1 to 5 bids would be returned.
It is possible to specify only a lower or a higher value.

If you specify only a lower value, the two dots ('..') are not needed and every item with at least that number of bids is returned.
  filter=bidCount:[1]

If you specify only a higher value, the two dots ('..') are required and every item with a number of bids up to that maximum is returned.
  filter=bidCount:[..5]

Note: This filter applies only to auction items

buyingOptions

Browse

Marketplace Insights:

filter=buyingOptions:{FIXED_PRICE|BEST_OFFER}

Only items offering the specified buying formats are returned. Multiple values can be used for this filter and are separated by the pipe symbol - '|'.

Note: This filter is defined at the leaf category level and should be used with a leaf category ID. If this filter is used with a top-level category ID, it won’t work and the filtered results won’t be included in the response body.

Valid Values:

- FIXED_PRICE - Items offered for a fixed-price (Buy It Now). These items can also be offered as an auction. Once a bid is placed, FIXED_PRICE is no longer available and the item is now only available as an auction. When this happens, that item will not be return using this filter.

- AUCTION - Items offered only as an auction whether they have bids or not.


BEST_OFFER - Items where the buyer can send the seller a price they're willing to pay for the item. The seller can accept, reject, or send a counter offer. For details about Best Offer, see Best Offer.

Note: This filter is not supported in the Marketplace Insights API.

- CLASSIFIED_AD - Items that have been listed on eBay but state that the final sales transaction is to be completed outside of the eBay environment.

charityOnly



filter=charityOnly:true

Only items associated with a charity are returned.

conditionIds



filter=conditionIds:{1000|1500}

Only items with the specified condition ID are returned. Multiple values can be used for this filter and are separated by the pipe symbol - '|'.

The conditionIds filter returns items of a specific condition that correspond to a numerical code, such as New (1000), Good (5000), and Seller Refurbished (2500).

For more information on item conditions for some popular eBay categories, see Item condition ID and name values and the Item conditions by category help topic.

conditions



filter=conditions:{NEW|USED}

Only items in the specified conditions are returned. Item condition values can vary by category. Multiple values can be used for this filter and are separated by the pipe symbol - '|'.

Unlike the conditionID filter, the conditions filter will not return items of a specific condition such as Good, Very Good, or Seller Refurbished. It will only return items that are categorized by the broader conditions of NEW and USED. To get results for specific conditions, please use the conditionID filters.

For more information on item conditions for some popular eBay categories, see the Item conditions by category help topic.
Valid Values (case sensitive):

- NEW

- USED

- UNSPECIFIED

deliveryCountry



filter=deliveryCountry:US

Only items that can be shipped to the specified country are returned.

Restriction: This filter is ignored when used with the pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit filters.
Valid Values (case sensitive): Two-character ISO 3166 Country Code.

deliveryOptions



filter=deliveryOptions:{SELLER_ARRANGED_LOCAL_PICKUP}

Only local pickup items are returned.

Requirement:This filter must be used with the pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit filters.

- SELLER_ARRANGED_LOCAL_PICKUP

deliveryPostalCode



filter=deliveryPostalCode:95125

Only items that can be shipped to the specified postal/zip code are returned.

Restriction: This filter is ignored when used with the pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit filters.

Requirement: This filter must be used with the deliveryCountry filter.
Example: filter=deliveryPostalCode:95125,deliveryCountry:US

excludeSellers



filter=excludeSellers:{rpsseller|bigSales}

Any items from the specified sellers are not returned in the response. Multiple values can be used for this filter and are separated by the pipe symbol - '|'.
Valid Values: The sellers' eBay user ID.

excludeCategoryIds



filter=excludeCategoryIds:{15032|31387}

Any item in the specified categories will not be returned. Multiple values can be used for this filter and are separated by the pipe symbol - '|'.

guaranteedDeliveryInDays



Not applicable

This filter value has been deprecated. eBay Guaranteed Delivery is no longer a supported feature on any marketplace.

itemEndDate



Marketing: 

getSimilarItems

filter=itemEndDate:[2018-11-14T07:47:48Z..2018-12-14T07:47:48Z]

Only items scheduled to end within the specified date-time range are returned. The first date-time value is the start of the range and the second date-time value is the end of the range. The start and end range value are separated by two dots ('..').
It is possible to only use a start range value or only use an end range value.

If only specifying a start range value, the two dots ('..') are not needed and every listing ending after that is returned.
filter=itemEndDate:[2018-11-14T07:47:48Z]

If only specifying the end range value, the two dots ('..') are required before the end range value and every listing ending before that is returned.
filter=itemEndDate:[..2018-12-14T07:47:48Z]
Valid Values: UTC Format (yyyy-MM-ddThh:mm:ss.sssZ) (ISO 8601 standard)

itemStartDate



filter=itemStartDate:[2018-11-14T07:47:48Z..2018-12-14T07:47:48Z]

Only items scheduled to start within the specified date-time range are returned. The first date-time value is the start of the range and the second date-time value is the end of the range. The start and end range value are separated by two dots ('..').

Note: This filter is based on the timestamp recorded by eBay the moment the listing became available.


If only specifying a start range value, the two dots ('..') are not needed and every listing starting after that is returned.


If only specifying the end range value, the two dots ('..') are required before the end range value and every listing starting before that is returned.



itemLocationCountry





filter=itemLocationCountry:US

Only items located in the specified country are returned.
Restrictions:


This filter is ignored when used with the pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit filters.


This filter cannot be used with the itemLocationRegion filter. If both filters are used, an error will occur.


Only one country code value can be used for this filter.

 Valid Values (case sensitive): Two-character ISO 3166 Country Code

itemLocationRegion


filter=itemLocationRegion:WORLDWIDE

Only items located in the specified region are returned.



This filter cannot be used with the itemLocationCountry filter. If both filters are used, an error will occur.


 Supported values vary by marketplace. See Valid itemLocationRegion Values for valid values for each marketplace.


 When using the itemLocationRegion=WORLDWIDE filter, it is recommended to include the X-EBAY-C-ENDUSERCTX header with both country and zip parameters (e.g., X-EBAY-C-ENDUSERCTX: contextualLocation=country=US,zip=95008). This enables complete and accurate filtering of ship-eligible items based on buyer location.

Omitting this may result in incomplete or zero results for some US-based listings.



ASIA


BORDER_COUNTRIES


CONTINENTAL_EUROPE


EUROPEAN_UNION


NORTH_AMERICA


UK_AND_IRELAND


WORLDWIDE

lastSoldDate


filter=lastSoldDate:[2018-08-30T00:00:00Z..2018-09-17T00:00:00Z]

Only listings ended within the date range period are returned.

maxDeliveryCost



filter=maxDeliveryCost:0

Only items with free shipping are returned.
Valid Values: 0 (zero)

paymentMethods



filter=paymentMethods:{CREDIT_CARD}

Only items that offer payment by credit card are returned.
Valid Values: CREDIT_CARD

pickupCountry



filter=pickupCountry:US

This filter, along with the three other pickup filters, sets the local pickup radius. Only items that are available through local pickup and within the pickup radius set by the user are retrieved.

Requirement: The method must include all the pickup filters (pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit) and the deliveryOptions filter.

pickupPostalCode



filter=pickupPostalCode:95125

This filter, along with the three other pickup filters, sets the local pickup radius. Only items that are available through local pickup and within the pickup radius set by the user are retrieved. The pickupPostalCode value is generally the postal code of the buyer's address.

Requirement: The method must include all the pickup filters (pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit) and the deliveryOptions filter.
Valid Values: A postal or zip code.

pickupRadius



filter=pickupRadius:25

This filter, along with the three other pickup filters, sets the local pickup radius. Only items that are available through local pickup and within the pickup radius set by the user are retrieved.

The pickupRadius value defines the distance that the buyer iswilling to travel (in miles or km) from the postal code defined in the pickupPostalCode filter to pick up the item.
Requirement: The method must include all the pickup filters (pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit) and the deliveryOptions filter.

pickupRadiusUnit



filter=pickupRadiusUnit:mi

This filter, along with the three other pickup filters, sets the local pickup radius. Only items that are available through local pickup and within the pickup radius set by the user are retrieved. The pickupRadiusUnit defines the distance measurement unit used for the pickup radius.

Requirement: The method must include all the pickup filters (pickupCountry, pickupPostalCode, pickupRadius, and pickupRadiusUnit) and the deliveryOptions filter.


mi


km

price





filter=price:[10..50]

Only items with prices within the specified price range are returned. This filter supports double data type values. The first double value is the lower monetary value and the second double value is the higher monetary value.

In the example below, only items priced from $10.00 to $50.00 would be returned. The lower and higher monetary value are separated by two dots ('..').
It is possible to only use a lower or a higher monetary value.

If you only specify a lower monetary value, the two dots ('..') are not needed and every item priced at or above that price is returned.

filter=price:[10]

If you only specify a higher monetary value, the two dots ('..') are required and every item priced
 below or at that price is returned.

filter=price:[..50]

Requirement: This filter must be used with the priceCurrency filter.
Example: filter=price:[50..500],priceCurrency:USD

priceCurrency





filter=priceCurrency:USD

Specifies the currency tied to the price.

Valid Values (case sensitive): The three-digit Currency codes (ISO 4217 standard).

Restriction: This filter is only needed if the price (range) filter is used.
For example: filter=price:[50..500],priceCurrency:USD

priorityListing


filter=priorityListing:true

Only items that are a part of a Promoted Listings campaign are retrieved.

Note: For this filter to have an effect, the sort option must be set to Best Match (default).

qualifiedPrograms



filter=qualifiedPrograms:{EBAY_PLUS|AUTHENTICITY_GUARANTEE|AUTHENTICITY_VERIFICATION}

Only items that are eligible for eBay qualified programs, such as EBAY_PLUS, AUTHENTICITY_GUARANTEE, and AUTHENTICITY_VERIFICATION, are returned.

Note: In order for the search method to return items for this container, the filters deliveryCountry and deliveryPostalCode must be present.

eBay Plus is a premium account option for buyers, which provides benefits such as fast free domestic shipping and free returns on selected items. Top-Rated eBay sellers must opt in to eBay Plus to be able to offer the program on qualifying listings. Sellers must commit to next-day delivery of those items

Note: eBay Plus is available only to buyers in Germany, Austria, and Australia. Authenticity Guarantee is available only for items purchased on eBay.com.

The eBay Authenticity Guarantee program enables third-party authenticators to perform authentication verification inspections on items such as watches and sneakers.

The eBay Authenticity Verification program returns listings from verified sellers.

- EBAY_PLUS

- AUTHENTICITY_GUARANTEE

- AUTHENTICITY_VERIFICATION

returnsAccepted



filter=returnsAccepted:true

When set to "true", only items that can be returned to the seller are returned. If this is null, items are returned regardless of the seller's return policy.
Valid Value: true

searchInDescription


filter=searchInDescription:true

Only items with a title or description matching the specified keyword are returned.

sellerAccountTypes



filter=sellerAccountTypes:{INDIVIDUAL}

or

filter=sellerAccountTypes:{BUSINESS}

Only items from the specified seller account type are returned in the response. The seller account type indicates if the seller is a business or an individual.

This is determined when the seller registers with eBay. If they register for a business account, they have a business account. If they register for a private account, they have an individual account. This designation is required by the tax laws in some countries.
This filter is supported on the following sites:
- EBAY_AT (Austria)

- EBAY_BE (Belgium)

- EBAY_CH (Switzerland)

- EBAY_DE (Germany)

- EBAY_ES (Spain)

- EBAY_FR (France)

- EBAY_GB (Great Britain)

- EBAY_IE (Ireland)

- EBAY_IT (Italy)

- EBAY_PL (Poland)

Restriction: You can filter by either BUSINESS or INDIVIDUAL. But you cannot filter by both.
- BUSINESS

- INDIVIDUAL

sellers



filter=sellers:{rpsSeller|bigSales}

Only items from the specified sellers are returned in the response. Multiple values can be used for this filter and are separated by the pipe symbol '|'.

Restriction: Running a search with more than 250 sellers will generate an error message. This filter limits the maximum number of sellers to 250.

## Valid itemLocationRegion Values

Supported values for the itemLocationRegion filter vary by marketplace. See the table below for valid values for each marketplace:

Marketplace

Valid Values

EBAY_US

NORTH_AMERICA, WORLDWIDE

EBAY_GB

EUROPEAN_UNION, CONTINENTAL_EUROPE, WORLDWIDE

EBAY_DE


EBAY_CA


EBAY_AU


EBAY_FR

EUROPEAN_UNION, CONTINENTAL_EUROPE, BORDER_COUNTRIES, WORLDWIDE

EBAY_IT


EBAY_ES


EBAY_BE


EBAY_AT


EBAY_CH


EBAY_NL


EABY_PL


EBAY_IE

EUROPEAN_UNION, CONTINENTAL_EUROPE, UK_AND_IRELAND, WORLDWIDE

EBAY_SG

ASIA, WORLDWIDE

EBAY_HK

ASIA, BORDER_COUNTRIES, WORLDWIDE

## Related topics

- API Documentation
Browse APIDeal APIFeed Beta APIFeed APIMarketing APIOffer APIOrder API

- Guides

- Related Docs
Using eBay RESTful APIsCommerce APIsDeveloper APIsFinding APIShopping API

### eBay for Developers.

Community ForumTechnical SupportAPIsFAQs

Copyright 1999—2026 eBay Inc. All rights reserved.
API License AgreementUser agreementPrivacy policyCookies

## 

#### Thank you for helping us to improve the eBay developer program.

While we are not able to respond directly to your comments, we will carefully review them to improve your experience with eBay developer program!

If you need help, contact Developer Technical Support .

