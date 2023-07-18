import datetime
import json
import logging
import re
import sys
from kbc.env_handler import KBCEnvHandler
from lib.client import cjClient
from lib.result import cjWriter

API_TOKEN_KEY = '#apiToken'
ADVERTISER_OR_PUBLISHER_KEY = 'advOrPub'
ENTITY_KEY = 'entityId'
QUERY_KEY = 'recordsQuery'
INCREMENTAL_KEY = 'incremental'
DATE_FROM_KEY = 'dateFrom'
DATE_TO_KEY = 'dateTo'
DATE_FIELD_KEY = 'dateField'

MANDATORY_PARAMS = [API_TOKEN_KEY, ADVERTISER_OR_PUBLISHER_KEY,
                    ENTITY_KEY, QUERY_KEY, DATE_FROM_KEY]


class cjRunner(KBCEnvHandler):

    def __init__(self):

        KBCEnvHandler.__init__(self, mandatory_params=MANDATORY_PARAMS)
        self.validate_config(MANDATORY_PARAMS)

        self.paramApiToken = self.cfg_params[API_TOKEN_KEY]
        self.paramAdvOrPub = self.cfg_params[ADVERTISER_OR_PUBLISHER_KEY]
        self.paramEntityId = self.cfg_params[ENTITY_KEY]
        self.paramQuery = self._sanitizeQuery(self.cfg_params[QUERY_KEY])
        self.paramIncremental = self.cfg_params[INCREMENTAL_KEY]
        self.paramDateTo = self.cfg_params[DATE_TO_KEY]
        self.paramDateFrom = self.cfg_params[DATE_FROM_KEY]
        self.paramDateField = self.cfg_params.get(DATE_FIELD_KEY,'EventDate')

        self.varDateTo = self.parseDates(self.paramDateTo, 'to')
        self.varDateFrom = self.parseDates(self.paramDateFrom, 'from')
        self.varDateRange = self.split_dates_to_chunks(self.varDateFrom, self.varDateTo,
                                                       5, strformat='%Y-%m-%dT%H:%M:%SZ')

        logging.info("Downloading commissions. Start date: %s, end date: %s." % (self.varDateFrom, self.varDateTo))

        self._validateParameters()
        self.prepareColumnsAndQuery()

        _tableDict = {
            'commissions': {
                'fields': self.varCommissionColumn,
                'primaryKey': ['commissionId']
            }
        }

        if self.varItemsColumns is not None:

            _tableDict['commissions-items'] = {
                'fields': self.varItemsColumns,
                'primaryKey': ['commissionItemId', 'commissionId']
            }

        self.client = cjClient(self.paramApiToken)
        self.writer = cjWriter(dataPath=self.data_path, tableDict=_tableDict, incremental=self.paramIncremental)

    def _sanitizeQuery(self, queryString):

        queryString = re.sub(r"items\s*\{", " items{", queryString)
        queryString = re.sub(r"verticalAttributes\s*\{", " verticalAttributes{", queryString)
        queryString = re.sub(r"\{\s+", '{', re.sub(r"\s+\}", '}', queryString))

        return re.sub(r'\s+', ',', re.sub(r'[^\d\w\{\}]', ' ', queryString).strip())

    def _getItems(self, queryString):

        regexString = r"items\{([^}]+)\}"

        itemsList = re.findall(regexString, queryString)
        if itemsList == []:

            itemsList = ['']

        return itemsList[0], re.sub(r'\s+', '', re.sub(regexString, '', queryString))

    def _getVerticalAttributes(self, queryString):

        regexString = r"verticalAttributes\{([^}]+)\}"

        vertAttrList = re.findall(regexString, queryString)
        if vertAttrList == []:

            vertAttrList = ['']

        return vertAttrList[0], re.sub(r'\s+', '', re.sub(regexString, '', queryString))

    @staticmethod
    def removeEmptyValues(listObj):

        outList = []

        for elemement in listObj:

            if elemement != '':

                outList += [elemement]

        return outList

    def prepareColumnsAndQuery(self):

        _items, queryNoItems = self._getItems(self.paramQuery)

        if _items.strip() == '':

            logging.info("No items detected in the input query.")
            self.varItemsColumns = None

        else:

            if 'commissionItemId' not in _items:

                _items = ','.join(['commissionItemId', _items])

            _itemsColumns = [c.strip() for c in _items.split(',')]
            _itemsColumns += ['commissionId']

            _itemsColumns = self.removeEmptyValues(_itemsColumns)

            self.varItemsColumns = _itemsColumns

        _vAttr, queryNoVertAttr = self._getVerticalAttributes(queryNoItems)

        if _vAttr.strip() == '':

            logging.info("No vertical attributes detected.")
            _vertAttrColumns = []

        else:

            _vertAttrColumns = ['verticalAttributes_' + v.strip() for v in _vAttr.split(',')]

        sanitizedQuery = self._sanitizeQuery(queryNoVertAttr)

        if sanitizedQuery == '':

            logging.error("No query detected in root query. Process exiting!")
            sys.exit(1)

        if 'commissionId' not in sanitizedQuery:

            sanitizedQuery = ','.join(['commissionId', sanitizedQuery])

        _commissionsColumns = [c.strip() for c in sanitizedQuery.split(',')]
        _commissionsColumnsAll = _commissionsColumns + _vertAttrColumns
        _commissionsColumnsAll = self.removeEmptyValues(_commissionsColumnsAll)

        self.varCommissionColumn = _commissionsColumnsAll

        _vAttrQuery = self._sanitizeQuery(_vAttr)
        _itemsQuery = self._sanitizeQuery(_items)
        _queryAll = sanitizedQuery

        if _vAttrQuery != '':

            _queryAll += ',verticalAttributes{' + _vAttrQuery + '}'

        if _itemsQuery != '':

            _queryAll += ',items{' + _items + '}'

        self.varRecordsQuery = _queryAll
        logging.debug("Query:")
        logging.debug(_queryAll)

    def _validateParameters(self):

        _correctTypes = {
            'ApiToken': str,
            'AdvOrPub': str,
            'EntityId': list,
            'Query': str,
            'Incremental': bool
        }

        for key in _correctTypes:

            param = eval("self.param" + key)
            paramCorrectType = _correctTypes[key]
            paramType = type(param)
            paramTypeBool = isinstance(param, paramCorrectType)

            if paramTypeBool is False:

                logging.error(f"Wrong type for parameter \"{key}\". Expected: {str(paramCorrectType)}, "
                              + f"got: {str(paramType)}")

                sys.exit(1)

        if self.paramAdvOrPub not in ('advertiser', 'publisher'):

            logging.error(
                "Parameter \"advOrPub\" must be one of \"advertiser\" or \"publisher\".")
            sys.exit(1)

        if self.varDateTo <= self.varDateFrom:

            logging.error("The upper boundary of date must be greater than the lower boundary!")
            sys.exit(1)

        if len(self.paramEntityId) == 0:

            logging.error("No entity IDs provided.")
            sys.exit(1)

    def parseDates(self, dateString, dateType):

        if dateString == '':

            if dateType == 'to':

                parsedDate = datetime.datetime.utcnow()

            else:

                logging.error("Parameter \"dateFrom\" can't be empty!")
                sys.exit(1)

        elif dateString in ('now', 'today'):

            if dateType == 'to':

                parsedDate = datetime.datetime.utcnow().date()

            else:

                logging.error("Parameter \"dateFrom\" can't be one of \"now, today\".")
                sys.exit(1)

        elif dateString == 'yesterday':

            parsedDate = datetime.datetime.utcnow().date() + datetime.timedelta(days=-1)

        elif 'days ago' in dateString or 'day ago' in dateString:

            _dateRelative = re.sub(r'\s|days|ago|day', '', dateString)

            try:

                _dateRelative = int(_dateRelative)

            except ValueError as e:

                logging.error("Incorrect specification of date. %s" % e)
                sys.exit(1)

            parsedDate = datetime.datetime.utcnow().date() - datetime.timedelta(days=_dateRelative)

        else:

            try:

                parsedDate = datetime.datetime.strptime(dateString, '%Y-%m-%d')

            except ValueError as e:

                logging.error("Error when parsing date value.")
                logging.error(e)
                sys.exit(1)

        if dateType == 'to':

            parsedDate += datetime.timedelta(days=1)

        return datetime.datetime.combine(parsedDate, datetime.datetime.min.time())

    def run(self):

        for timeRange in self.varDateRange:

            startDate = timeRange['start_date']
            endDate = timeRange['end_date']

            logging.info("Starting download for period from %s to %s." % (startDate, endDate))

            allData = self.client.getPagedCommissions(advOrPub=self.paramAdvOrPub,
                                                      entities=json.dumps(self.paramEntityId),
                                                      startDate=startDate, endDate=endDate,
                                                      dateField=self.paramDateField,
                                                      recordsQuery=self.varRecordsQuery)

            for obj in allData:

                commissionId = obj['commissionId']

                if 'items' in obj:

                    itemsList = obj['items']
                    del obj['items']

                    for item in itemsList:

                        item['commissionId'] = commissionId
                        self.writer.writerItems.writerow(item)

                flattenedObj = self.writer.flattenJSON(obj)
                self.writer.writerCommissions.writerow(flattenedObj)
