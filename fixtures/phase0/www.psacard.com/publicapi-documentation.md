---
url: https://www.psacard.com/publicapi/documentation
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl)
---

Professional Sports Authenticator (PSA) & PSA/DNA Authentication Services

-  Getting Started

-
 How It Works

 Video Tutorials

 Grading Standards

-  Pricing & Services

 Authentication & Grading

 Collectors Club


Team Store

-  Vault & Sell

 Vault

 Sell on eBay

 PSA Partner Offers

 PSA Verified Repacks


Set Registry

-  Research

 Cert Verification

 Population Report

 Auction Prices

 Price Guide

 Card Facts


Card Ladder

-  PSA Near Me

 Drop Off Events & Shows

 Dealer Directory

-  Start Submission


Home

Submissions

Orders

Collection & Vault

Vault Shipping

Request Center

Help & Support

Account



Getting Started


- How It Works

- Video Tutorials

- Grading Standards


Pricing & Services


- Authentication & Grading

- Collectors Club




Vault & Sell


- Vault

- Sell on eBay

- PSA Partner Offers

- PSA Verified Repacks




Research


- Cert Verification

- Population Report

- Auction Prices

- Price Guide

- Card Facts




PSA Near Me


- Drop Off Events & Shows

- Dealer Directory




- Home

- Submissions

- Orders

-   Collection & Vault

- Vault Shipping

- Request Center

- Help & Support

- Account

Sponsored Ads

# PSA Public API

Sign in or register for access to our API.

 TOPICS: Authentication API Methods Error Codes

## Overview

All PSA Public API requests must be made over HTTPS, and can accessed from https://api.psacard.com/publicapi/. View a list of available methods and test results.

For questions, please contact [email protected].

Review the PSA API End User Agreement

### Authentication

We use your PSA login credentials to generate an access token that can be then used to make calls to our REST API.

To get an access token you will need to sign in or register.

To use the token, you need to add an "Authorization" header with the value of "bearer <access token>" to your call replacing "<access token>" with your generated token. For example, here's sample code to call a method requesting Cert data by PSA Cert number:

- JQuery

- PHP

var settings = {
    "async": true,
    "crossDomain": true,
    "url": "https://api.psacard.com/publicapi/cert/GetByCertNumber/00000000",
    "method": "GET",
    "headers": {
          "authorization": "bearer <access token>"
    }
$.ajax(settings).done(function (response) {
    console.log(response);
});

$curl = curl_init();
curl_setopt($curl, CURLOPT_URL,"https://api.psacard.com/publicapi/cert/GetByCertNumber/00000000");
$authorization = "Authorization: bearer <access token>";
curl_setopt($curl, CURLOPT_HTTPHEADER, array('Content-Type: application/json' , $authorization ));
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
$result = curl_exec($curl);
curl_close ($curl);

#### API Methods

Available Methods

We currently offer access to data from Cert Verification for single item searches by cert number.

 Method Details & Testing

##### Error Codes

We use conventional HTTP response codes to indicate the success or failure of API requests.

Usually, a response code of 500 will indicate invalid credentials, though it may also indicate an error on our servers.

A 4xx response typical indicates the request path is incorrect or invalid.

A response code of 204 indicates empty request data (ie. missing cert number).

A successful API call will return a 200 response code, but that does not mean data was returned.

- If the request values were not in the expected format (such as a cert number containing non-numeric or too few characters), the response body will contain something similar to { "IsValidRequest": false, "ServerMessage": "Invalid CertNo" }.

- If no data is found, but the request values were formatted correctly, the response body will contain { "IsValidRequest": true, "ServerMessage": "No data found" }.

- If a cert lookup is successful, look for "IsValidRequest": true, "ServerMessage": "Request successful" amongst the rest of the data in the response body.

  © 2026 Collectors Universe, Inc. All rights reserved.

Subscribe to our newsletter

Sign up for the latest news, exclusive promos, events, and much more!

     Subscribe

###### Company

- Who We Are


- Press

- Careers

###### Resources

- Specials

- Forums

- Articles

###### For Businesses

- Authorized Dealers


- Advertising

- PSA Dealer/Sales

###### Privacy & Terms

- Privacy

- Your Privacy Choices

- PSA Guarantee

- Terms & Conditions

###### Support



- Find My Package

- FAQ

 © 2026 Collectors Holdings, Inc. All rights reserved.

