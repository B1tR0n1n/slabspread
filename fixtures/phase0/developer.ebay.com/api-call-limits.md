---
url: https://www.developer.ebay.com/develop/get-started/api-call-limits -> 301 https://www.developer.ebay.com/develop/api/sell/api_call_limits (developer.ebay.com -> 403)
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl, www host)
---

API Call Limits | eBay Developers Program

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








HomeDevelopAPIs

## Search Documentation 

- sell

- buy

Guides 

Release Notes

API Call Limits

Request Headers

Notification Topics

Response Status and Error Codes

Traditional API Errors

Post-Order API Errors

Listing Management

Inventory Mapping

Queries
- listingPreviewsCreationTaskById

Mutations
- startListingPreviewsCreation

Inventory API

inventory_item
- bulkCreateOrReplaceInventoryItem

- bulkGetInventoryItem

- bulkUpdatePriceQuantity

- getInventoryItem

- createOrReplaceInventoryItem

- deleteInventoryItem

- getInventoryItems

product_compatibility
- getProductCompatibility

- createOrReplaceProductCompatibility

- deleteProductCompatibility

inventory_item_group
- getInventoryItemGroup

- createOrReplaceInventoryItemGroup

- deleteInventoryItemGroup

listing
- bulkMigrateListing

- getSkuLocationMapping

- createOrReplaceSkuLocationMapping

- deleteSkuLocationMapping

offer
- bulkCreateOffer

- bulkPublishOffer

- getOffers

- createOffer

- getOffer

- updateOffer

- deleteOffer

- getListingFees

- publishOffer

- publishOfferByInventoryItemGroup

- withdrawOffer

- withdrawOfferByInventoryItemGroup

location
- getInventoryLocation

- createInventoryLocation

- deleteInventoryLocation

- disableInventoryLocation

- enableInventoryLocation

- getInventoryLocations

- updateInventoryLocation

Feed API

order_task
- createOrderTask

- getOrderTask

- getOrderTasks

inventory_task
- createInventoryTask

- getInventoryTask

- getInventoryTasks

schedule
- createSchedule

- deleteSchedule

- getLatestResultFile

- getSchedule

- getSchedules

- getScheduleTemplate

- getScheduleTemplates

- updateSchedule

task
- createTask

- getInputFile

- getResultFile

- getTask

- getTasks

- uploadFile

customer_service_metric_task
- createCustomerServiceMetricTask

- getCustomerServiceMetricTask

- getCustomerServiceMetricTasks

Media API

image
- createImageFromFile

- createImageFromUrl

- getImage

video
- createVideo

- getVideo

- uploadVideo

document
- createDocument

- createDocumentFromUrl

- getDocument

- uploadDocument

post_order
- uploadPostOrderDocument

- downloadPostOrderDocument

- removePostOrderDocument

Stores API

store
- getStoreCategories

- addStoreCategory

- renameStoreCategory

- deleteStoreCategory

- getStore

- getStoreTask

- getStoreTasks

- moveStoreCategory

Traditional Listing APIs

Add Listing
- AddItem

- AddItems

- AddFixedPriceItem

Second Chance Listing
- AddSecondChanceItem

Revise Listing
- ReviseItem

- ReviseFixedPriceItem

- ReviseInventoryStatus

- AddToItemDescription

Relist Listing
- RelistItem

- RelistFixedPriceItem

Verify Listing
- VerifyAddItem

- VerifyAddFixedPriceItem

- VerifyRelistItem

- VerifyAddSecondChanceItem

End Listing
- EndItem

- EndItems

- EndFixedPriceItem

Get Listing
- GetItem

- GetSellerList

- GetSellerEvents

Listing Pictures
- UploadSiteHostedPictures

Traditional Store APIs

POST
- GetStore

- SetStoreCategories

- GetStoreCategoryUpdateStatus

Listing Metadata

Metadata API

marketplace
- getAutomotivePartsCompatibilityPolicies

- getCategoryPolicies

- getClassifiedAdPolicies

- getCurrencies

- getExtendedProducerResponsibilityPolicies

- getHazardousMaterialsLabels

- getItemConditionPolicies

- getListingStructurePolicies

- getListingTypePolicies

- getMinimumListingPricePolicies

- getMotorsListingPolicies

- getNegotiatedPricePolicies

- getProductSafetyLabels

- getRegulatoryPolicies

- getReturnPolicies

- getShippingPolicies

- getSiteVisibilityPolicies

compatibilities
- getCompatibilitiesBySpecification

- getCompatibilityPropertyNames

- getCompatibilityPropertyValues

- getMultiCompatibilityPropertyValues

- getProductCompatibilities

shipping:marketplace
- getExcludeShippingLocations

- getHandlingTimes

- getShippingCarriers

- getShippingLocations

- getShippingServices

country
- getSalesTaxJurisdictions

Taxonomy API

category_tree
- fetchItemAspects

- getDefaultCategoryTreeId

- getCategoryTree

- getCategorySubtree

- getCategorySuggestions

- getItemAspectsForCategory

- getCompatibilityProperties


- getExpiredCategories

Charity API

charity_org
- getCharityOrg

- getCharityOrgs

Catalog API

product
- getProduct

product_summary
- search

Traditional Listing Metadata APIs

- GeteBayDetails

- GetItemShipping

- GetDescriptionTemplates

Account Management

Finances API

order_earnings
- getOrderEarnings

- getOrderEarningsById

- getOrderEarningsSummary

payout
- getPayout

- getPayouts

- getPayoutSummary

seller_funds_summary
- getSellerFundsSummary

transaction
- getTransactions

- getTransactionSummary

transfer
- getTransfer

billing_activity
- getBillingActivities

Account API v1

custom_policy
- createCustomPolicy

- getCustomPolicies

- getCustomPolicy

- updateCustomPolicy

fulfillment_policy
- createFulfillmentPolicy

- deleteFulfillmentPolicy

- getFulfillmentPolicies

- getFulfillmentPolicy

- getFulfillmentPolicyByName

- updateFulfillmentPolicy

payment_policy
- createPaymentPolicy

- deletePaymentPolicy

- getPaymentPolicies

- getPaymentPolicy

- getPaymentPolicyByName

- updatePaymentPolicy

payments_program
- getPaymentsProgram

- getPaymentsProgramOnboarding

privilege
- getPrivileges

program
- getOptedInPrograms

- optInToProgram

- optOutOfProgram

rate_table
- getRateTables

return_policy
- createReturnPolicy

- deleteReturnPolicy


- getReturnPolicy

- getReturnPolicyByName

- updateReturnPolicy

sales_tax
- bulkCreateOrReplaceSalesTax

- createOrReplaceSalesTax

- deleteSalesTax

- getSalesTax

- getSalesTaxes

subscription
- getSubscription

kyc
- getKYC

advertising_eligibility
- getAdvertisingEligibility

Account API v2

- getRateTable

- updateShippingCost

payout_settings
- getPayoutSettings

- updatePayoutPercentage

combined_shipping_rules
- createCalculatedShippingRules

- createFlatShippingRules

- createPromotionalShippingRule

- getCombinedShippingRules

- updateCalculatedShippingRules

- updateCombinedPayments

- updateFlatShippingRules

- updatePromotionalShippingRule

user_preferences
- getUserPreferences

- setUserPreferences

Traditional Sell User Account APIs

User Info
- GetUser

- GetUserContactDetails

- GetBidderList

Billing
- GetAccount

Selling Preferences
- GetUserPreferences

- SetUserPreferences

Shipping Discounts
- GetShippingDiscountProfiles

- SetShippingDiscountProfiles

Tax Tables
- GetTaxTable

- SetTaxTable

Selling Activity
- GetMyeBaySelling

User Notes
- SetUserNotes

User Authentication
- ConfirmIdentity

- FetchToken

- GetSessionID

- RevokeToken

- GetTokenStatus

Order Management

Fulfillment

order
- getOrder

- getOrders

- issueRefund

shipping_fulfillment
- getShippingFulfillments

- createShippingFulfillment

- getShippingFulfillment

payment_dispute
- getPaymentDispute

- fetchEvidenceContent

- getActivities

- getPaymentDisputeSummaries

- contestPaymentDispute

- acceptPaymentDispute

- uploadEvidenceFile

- addEvidence

- updateEvidence

Logistics API

shipment
- cancelShipment

- createFromShippingQuote

- downloadLabelFile

- getShipment

shipping_quote
- createShippingQuote

- getShippingQuote

Post-Order API

cancellation
- createCancellationRequest

- checkCancellationEligibility

- searchCancellations

- getCancellation

- approveCancellation

- rejectCancellation

casemanagement
- getCase

- appealCaseDecision

- searchCases

inquiry
- getInquiry

- escalateInquiry

- issueInquiryRefund

- provideInquiryShipmentInfo

- searchInquiries

- sendInquiryMessage

return
- searchReturns

- getReturn

- addShippingLabelInfo

- processReturnRequest

- escalateReturn

- uploadReturnFile

- getReturnFiles

- getReturnPreferences

- issueReturnRefund

- markItemReceived

- sendReturnMessage

- setReturnPreferences

- getShipmentTrackingInfo

- createReturnRequest

Traditional Sell Order Management APIs

- GetOrders

- GetItemTransactions

- GetSellerTransactions

- CompleteSale

- AddOrder

- SendInvoice

Offers and Leads

Leads API

classified_lead
- getAllClassifiedLeads

- getClassifiedLeadsByItemId

Traditional Offers and Leads APIs

- GetBestOffers

- RespondToBestOffer

- GetAllBidders

- GetAdFormatLeads

Communication

Message API

conversation
- bulkUpdateConversation

- getConversation

- getConversations

- sendMessage

- updateConversation

Notification API

config
- getConfig

- updateConfig

destination
- createDestination

- deleteDestination

- getDestination

- getDestinations

- updateDestination

public_key
- getPublicKey

- createSubscription

- createSubscriptionFilter

- deleteSubscription

- deleteSubscriptionFilter

- disableSubscription

- enableSubscription


- getSubscriptionFilter

- getSubscriptions

- testSubscription

- updateSubscription

topic
- getTopic

- getTopics

Negotiation API

- findEligibleItems

- sendOfferToInterestedBuyers

Feedback API

awaiting_feedback
- getItemsAwaitingFeedback

feedback
- getFeedback

- leaveFeedback

feedback_rating_summary
- getFeedbackRatingSummary

respond_to_feedback
- respondToFeedback

Traditional Sell Communication APIs

Message
- AddMemberMessageAAQToPartner

- AddMemberMessageRTQ

- AddMemberMessagesAAQToBidder

- DeleteMyMessages

- GetMemberMessages

- GetMessagePreferences

- GetMyMessages

- ReviseMyMessages

- ReviseMyMessagesFolders

- SetMessagePreferences

Feedback
- GetFeedback

- GetItemsAwaitingFeedback

- LeaveFeedback

- RespondToFeedback

Notifications
- GetNotificationPreferences

- GetNotificationsUsage

- SetNotificationPreferences

Marketing and Promotions

Marketing API

ad
- bulkCreateAdsByInventoryReference

- bulkCreateAdsByListingId

- bulkDeleteAdsByInventoryReference

- bulkDeleteAdsByListingId

- bulkUpdateAdsBidByInventoryReference

- bulkUpdateAdsBidByListingId

- bulkUpdateAdsStatus

- bulkUpdateAdsStatusByListingId

- getAds

- createAdByListingId

- createAdsByInventoryReference

- getAd

- deleteAd

- deleteAdsByInventoryReference

- getAdsByInventoryReference

- updateBid

- upsertVideoAdsPreferences

- bulkUpsertVideoAdsPreferences

ad_group
- getAdGroups

- createAdGroup

- getAdGroup

- updateAdGroup

- suggestBids

- suggestKeywords

campaign
- cloneCampaign

- getCampaigns

- createCampaign

- getCampaign

- deleteCampaign

- endCampaign

- findCampaignByAdReference

- getCampaignByName

- pauseCampaign

- resumeCampaign

- suggestBudget

- suggestItems

- suggestMaxCpc

- updateAdRateStrategy

- updateBiddingStrategy

- updateCampaignBudget

- updateCampaignIdentification

keyword
- bulkCreateKeyword

- bulkUpdateKeyword

- getKeywords

- createKeyword

- getKeyword

- updateKeyword

negative_keyword
- bulkCreateNegativeKeyword

- bulkUpdateNegativeKeyword

- getNegativeKeywords

- createNegativeKeyword

- getNegativeKeyword

- updateNegativeKeyword

ad_report
- getReport

ad_report_metadata
- getReportMetadata

- getReportMetadataForReportType

ad_report_task
- getReportTasks

- createReportTask

- getReportTask

- deleteReportTask

item_price_markdown
- createItemPriceMarkdownPromotion

- getItemPriceMarkdownPromotion

- updateItemPriceMarkdownPromotion

- deleteItemPriceMarkdownPromotion

item_promotion
- createItemPromotion

- getItemPromotion

- updateItemPromotion

- deleteItemPromotion

promotion
- getListingSet

- getPromotions

- pausePromotion

- resumePromotion

promotion_report
- getPromotionReports

promotion_summary_report
- getPromotionSummaryReport

email_campaign
- getEmailCampaigns

- createEmailCampaign

- getEmailCampaign

- updateEmailCampaign

- deleteEmailCampaign

- getAudiences

- getEmailPreview

- getEmailReport

Recommendation API

listing_recommendation
- findListingRecommendations

Analytics and Reporting

Analytics API

customer_service_metric
- getCustomerServiceMetric

seller_standards_profile
- findSellerStandardsProfiles

- getSellerStandardsProfile

traffic_report
- getTrafficReport

Other APIs

Identity API

user
- getUser

Translation API

language
- translate

eDelivery International Shipping API

actual_costs
- getActualCosts

address_preference
- getAddressPreferences

- createAddressPreference

agents
- getAgents

battery_qualifications
- getBatteryQualifications

bundle
- cancelBundle

- createBundle

- getBundle

- getBundleLabel

complaint
- createComplaint

consign_preference
- getConsignPreferences

- createConsignPreference

cpsc_profiles
- getCpscProfiles

dropoff_sites
- getDropoffSites

handover_sheet
- getHandoverSheet

labels
- getLabels

package
- bulkCancelPackages

- bulkConfirmPackages

- bulkDeletePackages

- cancelPackage

- clonePackage

- confirmPackage

- createPackage

- getPackage

- deletePackage

- getPackagesByLineItemID

services
- getServices

tracking
- getTracking

VeRO API

vero_reason_code
- getVeroReasonCode

- getVeroReasonCodes

vero_report
- createVeroReport

- getVeroReport

vero_report_items
- getVeroReportItems

VeRO API v2



report_vero_violations
- reportVeroViolations



App Settings & Insight

Developer Analytics API

rate_limit
- getRateLimits

user_rate_limit
- getUserRateLimits

Client Registration API

register
- registerClient

Key Management API

signing_key
- getSigningKeys

- createSigningKey

- getSigningKey

App Insights API 

- applicationApiRateLimits

- userApiRateLimits

- bulkDataTransferThresholds

## API Call Limits

eBay APIs support a large number of applications and serve billions of API calls every month. To maintain a high level of availability and provide superior quality of service, eBay limits the API call usage. The limits on the total calls and the rate at which the calls can be made depend on the API.

Our default API call limits are designed for individuals and smaller businesses. If your volume increases, you can get higher limits after completing our Application Growth Check.

After you join the eBay Developers Program and get your application keyset, you can start using eBay APIs immediately. The default call limits on the eBay APIs allow you to test and explore the API capabilities. Many applications are able to perform all capabilities using the default limits. If you need higher call limits, you can complete our Application Growth Check, to verify that your application is adhering to eBay's API License Agreement, and that you've made the most efficient use of the APIs you've implemented.

The following table provides the default API call limit rates for individuals and smaller businesses.

Functional Group

API Name

Default Call Limits


Account API

25,000 API calls per day


15,000 API calls per day



customer_service_metric resource: 400 API calls per day

seller_standards_profile resource, traffic_report resource: 100 API calls per day


Analytics APIs

5,000 API calls per day


Notification

10,000 API calls per day



100,000 API calls per day


2 Million API calls per day

Inventory Mapping API

20 API calls per day

Media

document resource: 1,000,000 API calls per day
POST rate user level limit: 50 requests per 5 seconds


Catalog†


Charity




Taxonomy


Marketing and Discounts

Merchandising API




Marketing Promotion API: 100,000 API calls per day

Marketing Ads API: 10,000 API calls per day





1 Million API calls per day


Fulfillment API

Order resource (all methods): 100,000 API calls per day

getPaymentDispute method: 250,000 API calls per day

getPaymentDisputeSummaries method: 250,000 API calls per day

Payment_dispute resource (all other methods): 250,000 API calls per day (combined limit for all methods)


2.5 Million API calls per day


Each resource within the Post-Order API has its own separate call limit:

- Cancellation: 5,000 API calls per day

- Case Management: 5,000 API calls per day

- Inquiry: 5,000 API calls per day

- Return: 5,000 API calls per day


Business Policies API
(deprecated)


Compliance API


Identity†


Product API


Product Metadata API


Trading API


Translation (beta)


* Buy APIs require an additional license. See the API documentation for details.

† Additional user restrictions apply. See the API documentation for details.

For OAuth token call limit details, see Access token rate limits and best practices.

## GraphQL API Rate Limits

Unlike REST APIs, which apply call limits at the API level, Public GraphQL rate limits are applied to individual root operation fields. Each root operation field (query or mutation) has its own default call limit, independent of other fields in the same operation.

The following table lists the default rate limits for Public GraphQL root operation fields.



Root Operation Field




query.listingPreviewsCreationTaskById


mutation.startListingPreviewsCreation


When a call exceeds its root-operation-field rate limit, the API returns HTTP 200 with a GraphQL execution-time error: extensions.errorCode = RATE_LIMITED. See the RATE_LIMITED error code in Response Status and Error Codes → GraphQL API Errors for details.

### eBay for Developers.

Community ForumTechnical SupportAPIsFAQs

Copyright 1999—2026 eBay Inc. All rights reserved.
API License AgreementUser agreementPrivacy policyCookies

## 

#### Thank you for helping us to improve the eBay developer program.

While we are not able to respond directly to your comments, we will carefully review them to improve your experience with eBay developer program!

If you need help, contact Developer Technical Support .

