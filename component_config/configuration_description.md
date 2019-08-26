The example of component's configuration can be foung in the [repository](https://bitbucket.org/kds_consulting_team/kds-team.ex-cj-affiliate/src/master/component_config/sample-config/).

The API returns commissions that satisfy a query sent to the API. The **full** query sent to the API might have the following form

```
{ publisherCommissions(forPublishers: ["999"], sinceEventDate:"2018-08-08T00:00:00Z",beforeEventDate:"2018-08-09T00:00:00Z"){count payloadComplete records {actionTrackerName websiteName advertiserName postingDate pubCommissionAmountUsd items { quantity perItemSaleAmountPubCurrency totalCommissionPubCurrency }  }  } }
```

but for simplicity reasons, the user is not required to provide full query, but rather configure a set of parameters, while the component takes care of the rest and builds the required query.

### Parameters

In the following section, each parameter will be dissected one-by-one and its role in the query explained. A sample version of the configuration file can be found [here](https://bitbucket.org/kds_consulting_team/kds-team.ex-cj-affiliate/src/master/component_config/sample-config/config.json).

##### Note on date ranges

By design, the CJ's API only accepts date ranges with a maximum of 31 days difference. The extractor automatically splits the date into intervals of maximum 10 days and queries the data for each of the 10-day ranges. A 10 day interval was chosen as an optimal trade-off between number of requests and long query times for longer date ranges.

##### Notes on pagination

All of responses by CJ's API return at most 10000 responses on a single page. A pagination is automatically handled by the extractor using the `sinceCommissionId` cursor parameter. Additionally, meta parameters `payloadComplete` and `maxCommissionId` are automatically added to the query for pagination purposes.

#### Personal Access Token (`#apiToken`)

The personal access token can be created in the [CJ's developer portal](https://developers.cj.com/account/personal-access-tokens) and provides access to one of the endpoints in CJ's API. The token is used to authenticate all requests. Each request is authenticated by appending personal access token in the `Authorization` header.

#### Advertiser or Publisher (`advOrPub`)

A string marking, whether to use `publisherCommissions` or `advertiserCommissions` endpoint. The default value is `advertiserCommissions`.

Depending on the value chosen, the first part of the query will differ. If `advertiser` is selected, the query will have a form of `{advertiserCommissions (forAdvertisers: ...) ...}`, otherwise it will take shape of `{publisherCommissions (forPublishers: ...) ...}`.

#### Entity IDs (`entityId`)

An array of entities for which the commissions should be downloaded. Only the authorized entities are downloaded (design of CJ's API). If the account used to authorize the request has no access to any of the entities specified, the component will fail.

Irrespectful of the endpoint chosen, the array of entities is filled directly after endpoint specification. The query thus might look like this:

```
{advertiserCommissions( forAdvertisers: ["12345678","23456789"] ...) ...}
```

#### Start Date (`dateFrom`)

A date, since when the commissions will be downloaded. The extractor is using the `sinceEventDate` field to query only the commissions satisfying the condition. Accepted values for the parameter are:

- `yesterday`,
- `X days ago` where `X` is a positive integer,
- or, an absolute date in format `YYYY-MM-DD`.

The parameter will be added to the query after the entities are specified, hence the query takes form of:

```
{advertiserCommissions( forAdvertisers: ["12345678","23456789"] sinceEventDate: "2019-01-01T00:00:00Z" ...) ...}
```

#### End Date (`dateTo`)

Similar to parameter `dateFrom`, the `dateTo` parameter defines a window, for which the commissions are downloaded. The parameter uses field `beforeEventDate` to filter the commissions. Accepted values are:

- `today` or `now`,
- `yesterday`,
- `X days ago` where `X` is a positive integer,
- or, an absolute date in format `YYYY-MM-DD`.

If left blank, the parameter defaults to `now`. Adding this parameter to the query completes the endpoint function specification. The query now has a form of:

```
{advertiserCommissions( forAdvertisers: ["12345678","23456789"] sinceEventDate: "2019-01-01T00:00:00Z" beforeEventDate: "2019-01-02T00:00:00Z") ...}
```

#### Incremental Load (`incremental`)

A boolean marking, whether incremental load to storage should be utilized. The parameter value does not affect the query or its shape, but rather effects load type used when exporting tables to Keboola Storage.

#### Query (`recordsQuery`)

A query used to specify fields to be returned by the API. The full list of available fields for both endpoints can be found in [the API's documentation](https://developers.cj.com/graphql/reference/Commission%20Detail). The query can be space, comma, dot or new-line separated string of fields and should represent the query used in `records` query field, which defines the response.

Queries can be split into 3 parts:

- main part,
- items part,
- vertical attributes part.

If specified, the items part of the query is outputted into a separate table called `commissions-items`. Main and vertical attributes parts are together bundled and provided in `commissions` table.

In addittion, if field `commissionId` is not specified in the query, it will automatically be added as it's used as a primary key for the `commissions` table. Similarly, if not specified, field `commissionItemId` is added for table `commissions-items`.

An example input can have the following form:

```
commissionId advertiserId saleAmountAdvCurrency items {sku} verticalAttributes{age, city, campaignId}
```

and fills in the last piece of puzzle into the query sent to the API:

```
{advertiserCommissions( forAdvertisers: ["12345678","23456789"] sinceEventDate: "2019-01-01T00:00:00Z" beforeEventDate: "2019-01-02T00:00:00Z") {payloadComplete maxCommissionId records {
    commissionId advertiserId saleAmountAdvCurrency items { commissionItemId sku} verticalAttributes{age, city, campaignId}
} } }
```

Notice the added `commissionItemId` field in the items query. The query inputted must not be encapsulated by curly braces (`{}`) as it's already inputted into `records {}`, which itself is bounded by these. The query will fail otherwise.

Correct:

```
commissionId advertiserId saleAmountAdvCurrency items { commissionItemId sku} verticalAttributes{age, city, campaignId}
```

Incorrect:

```
{ commissionId advertiserId saleAmountAdvCurrency items { commissionItemId sku} verticalAttributes{age, city, campaignId} }
```