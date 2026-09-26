---
url: https://www.developer.ebay.com/api-docs/user-guides/static/mip-user-guide/mip-enum-condition-descriptor-ids-for-trading-cards.html
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl, www host)
---

Condition Descriptor IDs for Trading Cards | eBay Developers Program

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








HomeDevelopAPI DocumentationCondition Descriptor IDs for Trading Cards

# Condition Descriptor IDs for Trading Cards

﻿

For cards in the three collectable card categories, 183050, 183454, and 261328, use numeric IDs to represent the professional grader (company) and the grade value, and optionally use an open text field for the Certification Number. For ungraded items, use numeric IDs to represent the condition. 

Condition Descriptors are used in the Product feed and the Combined feed.

The following table contains condition descriptor IDs for different conditions/condition IDs. See the Category support column for applicable condition descriptor IDs (values) for each category.

Condition

 (enumerated value)*

Condition descriptor display name

Condition descriptor ID**

Category support

Graded

LIKE_NEW

Professional Grader

27501 

Professional
 Grader IDs

Grade

27502

 IDs

Certification Number

27503

Certification
 Number field

Ungraded

USED_VERY_GOOD

Card Condition

40001

Ungraded Card Condition Descriptor IDs

* No new enumerated values were created, but these existing values are now also applied to trading cards in the Condition or conditionInfo.condition field.

** Used in the Condition Descriptor Name n (where n = 1-4) or the conditionDescriptor.name field.

## Professional grader IDs

Use the following IDs, as applicable for categories 183050, 183454, and 261328, representing the professional grader (27501) listed below.

Professional grader


ID*

183050

183454

261328

 Sports Authenticator (PSA)

X



275010

Beckett
 Collectors Club Grading (BCCG)




275011

 Vintage Grading (BVG)




275012

 Grading Services (BGS)




275013

Certified
 Sports Guaranty (CSG) 


275014

 Guaranty Company (CGC)




275015

Sportscard
 Guaranty Corporation (SGC)




275016

K
 Sportscard Authentication (KSA)




275017

Gem
 Mint Authentication (GMA)




275018

Hybrid
 Grading Approach (HGA)




275019

International
 Sports Authentication (ISA)




2750110

 Card Authenticator (PCA)


2750111

Gold
 Standard Grading (GSG)




2750112

Platin
 Grading Service (PGS)




2750113

MNT
 Grading (MNT)




2750114

Technical
 Authentication & Grading (TAG)




2750115

Rare
 Edition (Rare)




2750116

Revolution
 Card Grading (RCG)




2750117

Premier
 Card Grading (PCG)


2750118

Ace
 Grading (Ace)


2750119

Card
 Grading Australia (CGA)




2750120

Trading
 Card Grading (TCG)


2750121

ARK
 Grading (ARK)


2750122

Other




2750123

* Used in the Condition Descriptor Value n (where n = 1-4) or conditionDescriptor.value field with the name field of 27501.

## Grade IDs

Use the following IDs, for categories 183050, 183454, and 261328, representing the grade (27502) as listed below.



10

275020

9.5

275021

9

275022

8.5

275023

8

275024

7.5

275025

7

275026

6.5

275027

6

275028

5.5

275029

5

2750210

4.5

2750211

4

2750212

3.5

2750213

3

2750214

2.5

2750215

2

2750216

1.5

2750217

1

2750218

Authentic

2750219

Authentic Altered

2750220

Authentic - Trimmed

2750221

Authentic - Coloured

2750222

* Used in the Condition Descriptor Value n (where n = 1-4) or conditionDescriptor.value field with the name field of 27502.

## Certification Number field

Open text is passed in this field. This text provides additional information about a condition descriptor.

For trading cards, this field houses the optional Certification Number condition descriptor (27503) for graded cards in categories 183050, 183454, and 261328. Maximum length: 30.

Used in the Condition Descriptor Additional Info n (where n = 1-4) or conditionDescriptor.additionalInfo field with the name field of 27503.

## Ungraded Card Condition Descriptor IDs

Use the following IDs, as applicable for categories 183050, 183454, and 261328, representing the ungraded condition (40001).







Near
 Mint or Better




400010

Excellent



400011

Very
 Good



400012

Poor



400013

Lightly
 Played (Excellent)


400015

Moderately
 Played (Very Good)


400016

Heavily
 Played (Poor)


400017

* Used in the Condition Descriptor Value n (where n = 1-4) or conditionDescriptor.value field with the name field of 40001.

### eBay for Developers.

Community ForumTechnical SupportAPIsFAQs

Copyright 1999—2026 eBay Inc. All rights reserved.
API License AgreementUser agreementPrivacy policyCookies

## 

#### Thank you for helping us to improve the eBay developer program.

While we are not able to respond directly to your comments, we will carefully review them to improve your experience with eBay developer program!

If you need help, contact Developer Technical Support .

