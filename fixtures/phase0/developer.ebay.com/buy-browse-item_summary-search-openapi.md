---
url: https://www.developer.ebay.com/api-docs/master/buy/browse/openapi/3/buy_browse_v1_oas3.json (byte-identical to https://raw.githubusercontent.com/hendt/ebay-api/master/specs/buy_browse_v1_oas3.json)
html_reference: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search -> HTTP 403 on developer.ebay.com; www.developer.ebay.com 301 -> SPA https://www.developer.ebay.com/develop/api/buy/browse_api (reference text is loaded client-side; not present in fetched HTML)
fetched_at: 2026-09-26T00:24:49Z
status: 200 VERIFIED-BY-FETCH (official OpenAPI v1.20.4; excerpt of the search operation, its parameters, and condition-descriptor schemas)
---

Browse API OpenAPI spec (official): info.version = v1.20.4

== GET /item_summary/search : description ==
This method searches for eBay items by various query parameters and retrieves summaries of the items. You can search by keyword, category, eBay product ID (ePID), or GTIN, charity ID, or a combination of these.

<span class="tablenote"><b>Note:</b> Only listings where <code>FIXED_PRICE</code> (Buy It Now) is a buying option are returned by default. To retrieve listings that do not have <code>FIXED_PRICE</code> as a buying option, the <code>buyingOptions</code> filter can be used to retrieve those listings.

Note that an auction listing enabled with the <i>Buy it Now</i> feature will initially show <code>AUCTION</code> and <code>FIXED_PRICE</code> as buying options, but if/when that auction listing receives a qualifying bid, only <code>AUCTION</code> remains as a buying option. If this happens, the <code>buyingOptions</code> filter would need to be used to retrieve that auction listing.</span>
This method also supports the following:<ul><li>Filtering by the value of one or multiple fields, such as listing format, item condition, price range, location, and more. For the fields supported by this method, refer to the <a href="#uri.filter">filter</a> parameter.
<li>Retrieving the refinements (metadata) of an item, such as item aspects (color, brand) condition, category, etc. using the <a href="#uri.fieldgroups">fieldgroups</a> parameter.
<li>Filtering by item aspects and other refinements using the <a href="#uri.aspect_filter">aspect_filter</a> parameter.
<li>Filtering for items that are compatible with a specific product, using the <a href="#uri.compatibility_filter">compatibility_filter</a> parameter.
<li>Creating aspects histograms, which enables shoppers to drill down in each refinement narrowing the search results.

For additional information and examples of these capabilities, refer to <a href="/api-docs/buy/static/api-browse.html" target="_blank">Browse API</a> in the Buying Integration Guide.</br><h3>Pagination and sort controls</h3>There are pagination controls (<b>limit</b> and <b>offset</b> fields) and <b>sort</b> query parameters that control/sort the data that are returned. By default, results are sorted by <i>Best Match</i>. For more information about Best Match, refer to <a href="https://pages.ebay.com/help/sell/searchstanding.html " target="_blank">Best Match</a>.</br><h3>Restrictions</h3>This method can return a maximum of 10,000 items. For a list of supported sites and other restrictions, refer to <a href="/api-docs/buy/browse/overview.html#API">API Restrictions</a>.

<span class="tablenote"><b>eBay Partner Network:</b> In order to receive a commission for your sales, you must use the URL returned in the <code>itemAffiliateWebUrl</code> field to forward your buyer to the ebay.com site.</span>

== query parameter: aspect_filter ==
This field lets you filter by item aspects. The aspect name/value pairs and category, which is required, is used to limit the results to specific aspects of the item. For example, in a clothing category one aspect pair would be Color/Red.

<span class="tablenote"><b>Note:</b> The category ID must be specified <i>twice</i>:<ul><li>Once as a URI parameter in the <code>category_ids</code> field
<li>Once as part of the <code>aspect_filter</code> field

These two values <b>must</b> be the same.</span>
For example, to return items for a woman's red shirt, issue the following request:

    /buy/browse/v1/item_summary/search?q=shirt&category_ids=15724&aspect_filter=categoryId:15724,Color:{Red}
To get a list of the aspect pairs and the category, which is returned in the <code>dominantCategoryId</code> field, set <code>fieldgroups</code> to <code>ASPECT_REFINEMENTS</code> as illustrated here:
    /buy/browse/v1/item_summary/search?q=shirt&fieldgroups=ASPECT_REFINEMENTS
<span class="tablenote"><b> Note:</b> The pipe symbol is used as a delimiter between aspect filter values. If a value contains a pipe symbol (for example, the brand name 'Bed|Stü'), you must enter a backslash before the pipe character to prevent it from being evaluated as a delimiter.

The following example illustrates the correct format for entering two brand names as aspect filter values, one of which contains a pipe symbol:
    /buy/browse/v1/item_summary/search?limit=50&category_ids=3034&filter=buyingOptions:{AUCTION|FIXED_PRICE}&aspect_filter=categoryId:3034,Brand:{Bed\|Stü|Nike}
</span> For implementation help, refer to eBay API documentation at https://developer.ebay.com/api-docs/buy/browse/types/gct:AspectFilter

== query parameter: category_ids ==
<a name="category_ids"></a>The category ID is used to limit the results that are returned. This field may pass in one category ID or a comma separated list of IDs as illustrated in the following examples:
    /buy/browse/v1/item_summary/search?category_ids=29792

    /buy/browse/v1/item_summary/search?category_ids=267,29792
<span class="tablenote"><b>Note:</b> Currently, you can pass in only one category ID per request.</span>
To refine the set of information that is returned, <code>category_ids</code> may be combined with <b>EITHER</b>:<ul><li><code>epid</code> and/or <code>gtin</code> values
<li><code>q</code> keywords

For example, when looking of a toy phone, simply searching for "phone" will return mobile phones because that is the "Best Match" for the search. To further refine the request to include toy phones, include the <b>Toys & Hobbies</b> category ID as illustrated here:
    /buy/browse/v1/item_summary/search?q=phone&category_ids=220
Because the list of eBay category IDs is not published and category IDs are not the same across all eBay marketplaces, category IDs may be determined by:<ul><li>Visiting the <a href="https://pages.ebay.com/sellerinformation/news/categorychanges.html " target="_blank">Category Changes page</a>
<li>Using the Taxonomy API. Refer to <a href="/api-docs/buy/buy-categories.html" target="_blank">Get Categories for Buy APIs</a> for complete information.
<li>Issuing the following call to retrieve the <code>dominantCategoryId</code> for an item:
    /buy/browse/v1/item_summary/search?q=<i> keyword</i>&fieldgroups=ASPECT_REFINEMENTS


<span class="tablenote"><b>Note:</b> If a top-level (L1) category is specified, you <b>must</b> also include a <code>q</code> query parameter.</span>

== query parameter: fieldgroups ==
A comma-separated list of values that controls what is returned in the response. The default is <code>MATCHING_ITEMS</code>, which returns the items that match the keyword or category specified. The other values return data that can be used to create histograms or provide additional information.

<b>Valid Values:</b><ul><li><code>ASPECT_REFINEMENTS</code>
This field group adds the <a href="#response.refinement.aspectDistributions">aspectDistributions</a> container to the response.

<span class="tablenote"><b>Note:</b> Information returned by <code>ASPECT_REFINEMENTS</code> is category specific.</span>
<li><code>BUYING_OPTION_REFINEMENTS</code>
This field group adds the <a href="#response.refinement.buyingOptionDistributions">buyingOptionDistributions</a> container to the response.
<li><code>CATEGORY_REFINEMENTS</code>
This field group adds the <a href="#response.refinement.categoryDistributions">categoryDistributions</a> container to the response.
<li><code>CONDITION_REFINEMENTS</code>
This field group adds the <a href="#response.refinement.conditionDistributions">conditionDistributions</a> containers, such as <code>NEW</code>, <code>USED</code>, etc., to the response. Within these groups are multiple states of the condition.

For example, <code>NEW</code> can be <i>New without tag</i>, <i>New in box</i>, <i>New without box</i>, etc.
<li><code>EXTENDED</code>
This field group adds the following fields to the response:<ul><li><a href="/api-docs/buy/browse/resources/item_summary/methods/search#response.itemSummaries.shortDescription">shortDescription</a>
<li><a href="/api-docs/buy/browse/resources/item_summary/methods/search#response.itemSummaries.itemLocation.city">itemLocation.city</a>


<li><code>MATCHING_ITEMS</code> (<b>default value</b>)
This field group is intended to be used with one or more of the refinement values listed above. This is used to return the specified refinements and all matching items.
<li><code>FULL</code>
This field group returns all refinement containers and all matching items.

<b>Default:</b> <code>MATCHING_ITEMS</code>

== query parameter: filter ==
An array of field filters that can be used to limit/customize the result set.

Refer to <a href="/api-docs/buy/static/ref-buy-browse-filters.html" target="_blank">Buy API Field Filters</a> for additional information and examples of all supported filters.

For example, to filter shirts based on a specific range of prices, include the filter illustrated here: 
    /buy/browse/v1/item_summary/search?q=shirt&filter=price:[10..50]
Filters may also be combined within a single request as illustrated in the sample below which further refines results to return only those shirts available from specific sellers: 
    /buy/browse/v1/item_summary/search?q=shirt&filter=price:[10..50],sellers:{rpseller|bigSal}
 For implementation help, refer to eBay API documentation at https://developer.ebay.com/api-docs/buy/browse/types/cos:FilterField

== query parameter: limit ==
The number of items from the result set returned in a single page.

<span class="tablenote"><b>Note:</b> If a value is set in the <code>limit</code> field, the value of <code>offset</code> must be either zero or a multiple of the <code>limit</code> value. An error is returned for invalid <code>offset</code> values.</span>
<span class="tablenote"><b>Note:</b> This method can return a maximum of 10,000 items in one results set.</span>
<b>Min:</b> 1

<b>Max:</b> 200

<b>Default:</b> 50

== query parameter: q ==
A string consisting of one or more keywords used to search for items on eBay.

<span class="tablenote"><b>Note:</b> The <code>*</code> wildcard character is <b>not</b> allowed in this field.</span>
When providing two or more keywords in a single query, the string is processed as follows:<ul><li>When successive keywords are separated by a space, the list of keywords is processed as an <code>AND</code> request. For example, to retrieve items that include <b>both</b> of the keywords <b>iphone</b> AND <b>ipad</b>, submit the following query:

    /buy/browse/v1/item_summary/search?q=iphone ipad

<li>When successive keywords are comma-separated and surrounded by a single pair of parentheses, OR if the keywords are each URL-encoded, the list of keywords is processed as an <code>OR</code> request. For example, to retrieve items that include <b>iphone</b> OR <b>ipad</b>, submit one of the following queries:

    /buy/browse/v1/item_summary/search?q=(iphone, ipad)

    /buy/browse/v1/item_summary/search?q=%28iphone%2c%20ipad%29



<span class="tablenote"><b>Note:</b> When specifying keywords using the <code>q</code> parameter:<ul><li> <i>Do not include</i> an <code>epid</code> or <code>gtin</code> parameter value as neither can be used in conjunction with a keyword search.
<li>Strings longer than 100-characters are truncated.

</span>

<b>Maximum length:</b> 100 characters

== schema ItemSummary (search results) properties ==
additionalImages, adultOnly, availableCoupons, bidCount, buyingOptions, categories, compatibilityMatch, compatibilityProperties, condition, conditionId, currentBidPrice, distanceFromPickupLocation, energyEfficiencyClass, epid, image, itemAffiliateWebUrl, itemCreationDate, itemEndDate, itemGroupHref, itemGroupType, itemHref, itemId, itemLocation, itemOriginDate, itemWebUrl, leafCategoryIds, legacyItemId, listingMarketplaceId, marketingPrice, pickupOptions, price, priceDisplayCondition, priorityListing, qualifiedPrograms, seller, shippingOptions, shortDescription, thumbnailImages, title, topRatedBuyingExperience, tyreLabelImageUrl, unitPrice, unitPricingMeasure, watchCount

ItemSummary.condition: The text describing the condition of the item, such as <b>New</b> or <b>Used</b>. For a list of condition names, refer to <a href="/api-docs/sell/static/metadata/condition-id-values.html " target="_blank">Item Condition IDs and Names</a>.
ItemSummary.conditionId: The identifier of the condition of the item. For example, <code>1000</code> is the identifier for <code>NEW</code>. For a list of condition names and IDs, refer to <a href="/api-docs/sell/static/metadata/condition-id-values.html " target="_blank">Item Condition IDs and Names</a>.

== schemas that carry a conditionDescriptors property ==
Item.conditionDescriptors: This array is used by the seller to provide additional information about the condition of an item in a structured format. Condition descriptors are name-value attributes that indicate details about a particular condition of an item.

<span class="tablenote"><b>Note:</b> Condition descriptors are currently only available for the following trading card categories:<ul><li>Non-Sport Trading Card Singles
<li>CCG Individual Cards
<li>Sports Trading Card Singles

</span>

== schema ConditionDescriptor ==
This type displays additional information about the condition of an item in a structured format.
 - name: The name of a condition descriptor. The value(s) for this condition descriptor is returned in the associated <b>values</b> array.
 - values: This array displays the value(s) for a condition descriptor (denoted by the associated <b>name</b> field), as well as any other additional information about the condition of the item.

== schema ConditionDescriptorValue ==
This type displays the value(s) associated with the specified condition descriptor name, as well as any additional information about a condition descriptor. 
 - additionalInfo: Additional information about the condition of an item as it relates to a condition descriptor. This array elaborates on the value specified in the <b>content</b> field and provides additional details about the condition of an item.
 - content: The value for the condition descriptor indicated in the associated <b>name</b> field.