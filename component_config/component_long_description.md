# CJ Affiliate Extractor

CJ Affiliate is an online advertising company operating in the affiliate marketing industry, which operates worldwide. The extractor allows to connect to CJ's API and download commissions for specified advertisers or publishers.

The extractor utilizes [Commission Detail API](https://developers.cj.com/graphql/reference/Commission%20Detail) to query and download all commissions within specified time window. Both `publisherCommissions` and `advertiserCommissions` endpoints are available in the extractor.

#### Pre-requisities

To successfully run the extractor and download commissions, the following is required:
- personal access token,
- access to either `publisherCommissions` or `advertiserCommissions` endpoint.

The personal access token can be created in the [CJ's developer portal](https://developers.cj.com/account/personal-access-tokens).