---
url: https://community.ebay.com/t5/RESTful-Buy-APIs-Browse/Searching-for-PSA-10-graded-cards-only-in-the-Pokemon-TCG/td-p/34789291
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl)
---

Skip to main content

- 

- Home

- News & Updates

Buying & Selling

- Buying

- Selling

- New to selling on eBay

- Seller Tools

- Shipping

- Returns

- eBay Advertising

- Payments

- Mobile Apps

Explore Categories

- eBay Categories
- eBay Motors

- Electronics

- Collectibles & Art

- Home & Garden

- Clothing, Shoes & Accessories

- Toys & Hobbies

- Sporting Goods

- Books, Movies & Music

- Health & Beauty

- Business & Industrial

- Jewelry & Watches

- Specialty Services

- Special Categories
- eBay Partner Network

- Accessibility

- eBay Cafe

- Private Groups
- eBay Live

- Community Mentors

- eBay Developers Program
- APIs Feedback, Comments and Suggestions

- Post Order APIs

- RESTful Buy APIs

- RESTful Sell APIs

- Token, Messaging, Sandbox Related Issues

- Traditional APIs

- eBay APIs

- Ask a Mentor

About

- About the Community

- Share Community Platform Feedback

- Report eBay Technical Issues

- About eBay

Community Events

- Events

- Seller Circle Hosts

- Seller Circles

- eBay Help



All PostsDiscussionsBlogsIdeasQuestions










Categories







MoreDiscussions

Searching for PSA 10 graded cards only in the Pokemon TCG | Browse | eBay Community




- Browse

Searching for PSA 10 graded cards only in the Pokemon TCG
I'm trying to build a search query that only finds Pokemon TCG cards with a PSA grade of 10 but running into issues. I've tried a variety of query params to no avail. 

My current setup is:

```

curl --location --globoff 'https://api.ebay.com/buy/browse/v1/item_summary/search?q=pokemon&limit=50&sort=endingSoonest&filter=buyingOptions%3A{FIXED_PRICE}%2CconditionIds%3A{2750}&category_ids=183454&aspect_filter=conditionDescriptors.name%3AProfessional%20Grader%2CconditionDescriptors.values.content%3AProfessional%20Sports%20Authenticator%2CconditionDescriptors.name%3AGrade%2CconditionDescriptors.values.content%3A10' \


Where my `aspect_filter` is conditionDescriptors.name:Professional Grader,conditionDescriptors.values.content:Professional Sports Authenticator,conditionDescriptors.name:Grade,conditionDescriptors.values.content:10

But I get a warning 

"warnings": [

{

"errorId": 12017,

"domain": "API_BROWSE",

"category": "REQUEST",

"message": "The 'aspect_filter' query parameter must include a categoryId. For information, see the API call reference documentation."

}

],

Is this type of search even possible for the browse API? The condition ID includes PSA 9 cards that I do not want. I can adjust the query but some are still seeping into my results. 

For a cleaner way to see how I'm building my query here are the params before url encoding


return this.search({

q: query,

limit: limit.toString(),

sort: "endingSoonest",

filter: "buyingOptions:{FIXED_PRICE},conditionIds:{2750},grade:{10}",

category_ids: "183454",

aspect_filter: [

"conditionDescriptors.name:Professional Grader", // Correctly specify the name for the grader

"conditionDescriptors.values.content:Professional Sports Authenticator (PSA)", // Correctly specify the value for the grader

"conditionDescriptors.name:Grade", // Correctly specify the name for the grade

"conditionDescriptors.values.content:275020" // Use the correct grade ID for 10

].join(',')

});


dave12345222

Posted 1 year ago·Last reply 1 year ago

1 comment

Comment

Newest

OP1 year ago

https://developer.ebay.com/api-docs/user-guides/static/mip-user-guide/mip-enum-condition-descriptor-ids-for-trading-cards.html is somewhat helpful but not sure how to incorporate that into my request. 




