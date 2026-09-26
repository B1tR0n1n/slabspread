---
url: https://www.developer.ebay.com/updates/newsletter/q4_2023
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl, www host)
---

Newsletter | eBay Developers Program

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








HomeUpdatesNewsletterQ4 2023

# eBay Developers Program Q4 2023 Newsletter

- Program news

- Developer survey

- Condition Grading mandates for trading cards

- Revamped Making a Trading Call guide

- API updates

- API support for offsite Promoted Listings ads

- New dynamic bid rates for PLA campaigns

- Filters added to PL Report Metadata methods

- Charity and tax info returned in Finances API

- New userId field added to Browse API

- New itemOnHold boolean added to Order APIs

- New metric added to getTrafficReport

- API changes for actioned listings

- eBay Deprecation and Decommission updates

## Program news

We hope everyone is well. We want to take this time to share with you some updates that have occurred within the eBay Developers Program over the last quarter (October - December 2023). 

### Developer survey

Thank you to everyone who participated in our Developer Survey this fall! Your feedback is very valuable to us and helps us address any issues and improve our Developers Program in all aspects. Please be on the lookout for more surveys in the near future. Invitations to surveys are sent out to the contact email on file for each developer account.

### Condition Grading mandates for trading cards

The condition grading mandate for new listings went into effect in Q4. The item condition for all new trading card listings in Non-Sport Trading Card Singles (183050), Collectible Card Games Individual Cards (183454), and Sports Trading Card Singles (261328) categories must be either Graded (Condition ID 2750) or Ungraded (Condition ID 4000), and no other item conditions will be accepted. The following operations will fail if these item conditions are not used along with the applicable condition descriptor metadata: 

- Trading API calls: AddItem, AddFixedPriceItem, AddItems, RelistItem, RelistFixedPriceItem, VerifyAddItem, VerifyAddFixedPriceItem, and VerifyRelistItem

- Inventory API methods: bulkPublishOffer, publishOffer, and publishOfferByInventoryItemGroup

- Sell Feed API upload feed types: LMS_ADD_ITEM, LMS_ADD_FIXED_PRICE_ITEM, LMS_RELIST_ITEM, LMS_RELIST_FIXED_PRICE_ITEM, LMS_VERIFY_ADD_ITEM,and LMS_VERIFY_ADD_FIXED_PRICE_ITEM

Beginning on January 22, 2024, active trading card listings cannot be revised without updating the listings with Graded (Condition ID 2750) or Ungraded (Condition ID 4000) item conditions, and adding applicable condition descriptor metadata. The following operations will fail if these item conditions are not used along with the applicable condition descriptor metadata: 

- Trading API calls: ReviseItem and ReviseFixedPriceItem 

- Inventory API method: updateOffer

- Sell Feed API upload feed types: LMS_REVISE_ITEM and LMS_REVISE_FIXED_PRICE_ITEM

Condition descriptor metadata is provided through the ConditionDescriptors container in the Trading API or through the conditionDescriptors array in the Inventory API. For Graded cards, the professional grader and grade are needed, and for Ungraded cards, the card condition is needed. The getItemConditionPolicies method of the Metadata API must be used to retrieve the numeric identifiers used to provide condition descriptor name-value pairs.

### Revamped Making a Trading Call guide

A revamped Making a Trading API Call Guide has been published! The look and feel of the guide has been modernized and uses the same styles, navigation, and search as other guides on the developer portal. 

## API updates

The following updates have been made to our APIs over the last few months.

### API support for offsite Promoted Listings ads

The Sell Marketing API was enhanced to support offsite Promoted Listings ads. Offsite ads will appear on major search engines, and cost-per-click is the only supported funding model. An offsite ad campaign is created the same way as a regular “on-site” PLA campaign. 

Here are some key schema changes associated with offsite ads being enabled:

- The channels field was added to the createCampaign method in order to specify the PLA campaign as ON_SITE or OFF_SITE. 

- The channels field was added to createReportTask method in order to support Promoted Listings Reports for offsite ads.

- A new suggestBudget method was added to help the seller determine an optimal daily budget.

This feature is not available to all sellers, but the getAdvertisingEligibility method of the Account API v1 can be used to see if a seller is eligible for offsite ads. In the response of that method, the programType value will show as OFFSITE_ADS, and the status value will either show as ELIGIBLE or INELIGIBLE.

Currently, sellers are limited to one active offsite ad campaign at a time.

See the Offsite ads integration guide topic for more information on offsite ad campaigns.

### New dynamic bid rates for PLA campaigns

The Sell Marketing API now supports the ability to use dynamic bid rates for keywords in PLA campaigns. With dynamic bid rates, the seller is agreeing to letting eBay set and adjust keyword bid rates on a daily basis. 

Here are some key schema changes associated with dynamic bid rates being enabled:

- The biddingStrategy field was added to createCampaign method, and DYNAMIC is specified as the value to enable dynamic bidding. 

- The updateBiddingStrategy method was created in order to change the bidding strategy from FIXED to DYNAMIC, or vice versa. 

### Filters added to PL Report Metadata methods

Two new query parameters, funding_model and channel, were added to the getReportMetadata and getReportMetadataForReportType methods. With these two new filters, users have the ability to only retrieve specific metadata based on funding model and channel. They can use these filters to retrieve only Cost-per-sale report metadata, on-site Cost-per-click report metadata, or offsite Cost-per-click report metadata.

### Charity and tax info returned in Finances API

The following two updates were made to the Finances API:

- The donations container was added to the getTransactions response. This container will be returned for any line item in the order where a charitable donation was made as a result of the sale and shows the amount that will go to the charitable organization. To account for the debit against the seller’s account, the CHARITY_DONATION enum value was added to the FeeTypeEnum type.

- The taxes container was added to the getTransactions response. This container will be returned if the seller purchased an eBay shipping label, and tax was charged against this shipping label. The taxes container shows the amount and type of tax, as defined in the new TaxTypeEnum type.

### New userId field added to Browse API

A new seller.userId field added to the responses of the getItem, getItemByLegacyId, and getItemsByItemGroup methods in Browse API. This new ID is the seller’s immutable ID that cannot be changed like eBay user names. In order for this field to be returned, the fieldgroups query parameter must be included with a value of ADDITIONAL_SELLER_DETAILS. 

### New itemOnHold boolean added to Order APIs

A new itemOnHold boolean field has been added to the getGuestPurchaseOrder response of Order V2 API and to the getPurchaseOrder response of Order V1 API. This field will be returned as true if a listing associated with a line item has been put on hold due to a violation of eBay Policy.

### New metric added to getTrafficReport

A new metric, TOTAL_IMPRESSION_TOTAL, has been added to the getTrafficReport method of Sell Analytics API. This value is the total number of times the seller's listings have displayed on any page or flow and matches the value on the Seller Hub performance/traffic page. The existing LISTING_IMPRESSION_TOTAL metric only includes views in search results and in the seller’s eBay store.

To view this new metric, the user can pass in the TOTAL_IMPRESSION_TOTAL metric value through the metric query parameter of getTrafficReport.

### API changes for actioned listings

As a part of our continuous work to improve our notice and action programs, eBay has enabled changes to the reporting mechanisms on all eBay listings on all marketplaces.

eBay evaluates and reviews all reports, and when eBay decides to take action against a listing, the listing will be hidden. Hidden listings will be hidden from search, and any attempted purchases, offers, or bids will be blocked. Users that have a transactional relationship with the listing will have limited visibility to the hidden listing. In some circumstances, depending on the policy that was violated, eBay will give sellers the opportunity to address the violation and get listings fully reinstated, where possible. Users will be able to appeal listings actions, but there is not an API solution for that yet (planned for early next year). The appeals window default is 6 months, but will require the user to submit via the in-product webform until the API solution is available.

Numerous ‘GET’ operations that retrieve eBay listing data have been updated with warnings and or flags to indicate when a specific listing is hidden, and some item-level data, such as item title and photo URLs will be masked. The table below summarizes the updates to our APIs:

API

Operation

Schema and/or Behavior Change

Trading

GetItem

For visible on-hold listings

New SellingStatus.ListingOnHold boolean.

For hidden on-hold listings

New error message: "This listing has been removed for a policy violation.” with the following URL in ErrorParameters https://www.ebay.com/help/account/regulatory/regulatory-hub?id=5393"

GetItemTransactions

Existing Trading error code 17 used: “This item cannot be accessed because the listing has been deleted or you are not the seller.”

GetOrders and 

GetOrderTransactions

Existing Trading error code 21917182 used: “OrderLineItemIDs <ORDER_ID> could not be found. Associated Items may have been deleted or removed.”

GetSellerList 

Transactions from hidden listing not returned. No other changes.

GetSellerEvents

Item.Title field returned as ‘*****************’.

GetSellerTransactions and 

GetMyeBaySelling

The Item ID value of the listing is displayed in the Item.Title field.

Inventory

getOffer and getOffers

New listing.listingOnHold boolean.

Fulfillment

getOrder and getOrders

The Item ID value of the listing is displayed in the lineItems.title field.

getPaymentDispute

New buyerProvided.contentOnHold boolean.

Post-Order

Get Inquiry and 

Search Inquiries

New inquiryContentOnHold boolean.

New itemDetails.itemOnHold boolean.

itemDetails.itemTitle and itemDetails.itemPictureUrl masked with ‘*****************‘.

Get Return and 

Search Returns

New returnContentOnHold boolean.

New itemDetail.itemOnHold boolean.

Get Case and 

Search Cases

New caseContentOnHold boolean

Note: The initial solution for sellers to view and take action on hidden listings will be a landing page accessible through My eBay and Seller Hub.

### eBay Deprecation and Decommission updates

The following APIs/methods/fields have recently been announced as deprecated. Please see the Deprecation Status page for detailed information.

- The GetOrderTransactions call is deprecated and will be decommissioned on January 31, 2024. Developers have the option of migrating to the GetOrders call in the Trading API, or the getOrders method of the Fulfillment API. Please note that the Fulfillment API only returns paid orders, so if your use case calls for retrieving both paid and unpaid orders, we recommend migrating to the GetOrders call in the Trading API.

- Numerous response fields in the GetOrders, GetItemTransactions, GetSellerTransactions, and GetMyeBaySelling calls of the Trading API have been deprecated and will be decommissioned on January 31, 2024. For the full list of deprecated fields, and the reasons why they are being deprecated, see the Deprecated Trading Order Management Fields document.

- The GetSellerDashboard call of the Trading API is deprecated and will be decommissioned on April 2, 2024.The alternative to this call is the Seller Standards Profile methods of the Seller Analytics API.

- The suppressViolation method of the Compliance API is deprecated and will be decommissioned on January 30, 2024.

- The GetSuggestedCategories call of the Trading API is deprecated and will be decommissioned on July 1, 2024.The alternative to this call is the getCategorySuggestions method of the Taxonomy API. 

- The Return Management API is deprecated with the decommission date yet to be determined. The Post-Order API should be used to manage return requests.

- The UpdateReturnPolicy and UpdateSellerInfo fields in the ReviseItem call are deprecated and will be decommissioned on February 26, 2024.

- The CalculatedShippingRate.OriginatingPostalCode field in the Add Item family of calls is deprecated and will be decommissioned on February 26, 2024. This field will also stop being returned by some ‘Get’ calls as well. Please see the Deprecation Status page for full details.

- The ProductListingDetails.TicketListingDetails and Item.QuantityInfo containers in the Add Item family of calls are deprecated and will be decommissioned on February 26, 2024.

- The following four fields in GetMyeBaySelling are deprecated and will be decommissioned on February 6, 2024:

- Summary.AuctionBidCount

- Summary.ClassifiedAdOfferCount

- Summary.TotalLeadCount

- SellingSummary.AuctionBidCount

We hope everyone had an outstanding year, and we are looking forward to working with the community in 2024! 

### eBay for Developers.

Community ForumTechnical SupportAPIsFAQs

Copyright 1999—2026 eBay Inc. All rights reserved.
API License AgreementUser agreementPrivacy policyCookies

## 

#### Thank you for helping us to improve the eBay developer program.

While we are not able to respond directly to your comments, we will carefully review them to improve your experience with eBay developer program!

If you need help, contact Developer Technical Support .

