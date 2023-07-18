import logging
import sys
from kbc.client_base import HttpClientBase

BASE_URL = 'https://commissions.api.cj.com/query'


class cjClient(HttpClientBase):

    def __init__(self, token):

        self.paramToken = token

        _defaultHeaders = {
            'Authorization': ' '.join(["Bearer", self.paramToken])
        }

        HttpClientBase.__init__(self, base_url=BASE_URL, default_http_header=_defaultHeaders,
                                status_forcelist=(502, 504), max_retries=5)

        logging.debug("Client initialized.")

    def _sendQuery(self, query):

        rspQuery = self.post_raw(url=self.base_url, data=str(query), timeout=(60, 600))
        querySc, queryJs = rspQuery.status_code, rspQuery.json()

        if querySc == 200:

            if queryJs['data'] is None:

                logging.error(
                    "Empty data received. API response: %s" % queryJs)
                sys.exit(1)

            else:

                return queryJs['data']

        else:

            logging.error(
                "There was an error downloading commissions. Received: %s - %s " % (querySc, queryJs))
            sys.exit(1)

    def _buildQuery(self, advOrPub, entities, startDate,
                    endDate, dateField,  recordsQuery, sinceCommissionId=None):

        query = '{'

        if advOrPub == 'advertiser':

            query += f'advertiserCommissions ( forAdvertisers: {entities}, '

        else:

            query += f'publisherCommissions ( forPublishers: {entities}, '

        query += f'since{dateField}: "{startDate}", '
        query += f'before{dateField}: "{endDate}"'

        if sinceCommissionId is not None:

            query += f', sinceCommissionId: "{sinceCommissionId}"'

        query += ') { payloadComplete maxCommissionId records { '
        query += recordsQuery
        query += ' } } }'

        return query

    def getPagedCommissions(self, advOrPub, entities, startDate,
                            endDate, dateField, recordsQuery):

        dataKey = "advertiserCommissions" if advOrPub == 'advertiser' else "publisherCommissions"
        payloadComplete = False
        sinceCommissionId = None
        allData = []

        while payloadComplete is False:

            query = self._buildQuery(advOrPub, entities, startDate,
                                     endDate, dateField, recordsQuery, sinceCommissionId=sinceCommissionId)

            logging.info("Sending query: %s." % query)

            rspQuery = self._sendQuery(query)
            data = rspQuery[dataKey]
            payloadComplete = data['payloadComplete']
            sinceCommissionId = data['maxCommissionId']
            allData += data['records']

        return allData
