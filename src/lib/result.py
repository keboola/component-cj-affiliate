import csv
import json
import logging
import os
import sys
from kbc.result import KBCResult, KBCTableDef


class cjWriter:

    def __init__(self, dataPath, tableDict, incremental):

        self.paramDataPath = dataPath
        self.paramTableDict = tableDict
        self.paramIncremental = incremental
        self.run()

    def createTableDefinition(self, tableName, tableColumns, tablePK):

        _fileName = tableName + '.csv'
        _fullPath = os.path.join(
            self.paramDataPath, 'out', 'tables', _fileName)

        _tableDef = KBCTableDef(
            name=tableName, columns=tableColumns, destination=tableName, pk=tablePK)
        _resultDef = KBCResult(file_name=_fileName,
                               full_path=_fullPath, table_def=_tableDef)

        return _resultDef

    @staticmethod
    def createWriter(tableDefinition):

        _writer = csv.DictWriter(open(tableDefinition.full_path, 'w'),
                                 fieldnames=tableDefinition.table_def.columns,
                                 restval='', extrasaction='ignore',
                                 quotechar='"', quoting=csv.QUOTE_ALL)

        _writer.writeheader()

        return _writer

    @staticmethod
    def createManifest(destination, pk=[], incremental=False):

        _manifest = {'primary_key': pk, 'incremental': incremental}

        with open(destination, 'w') as _manFile:

            json.dump(_manifest, _manFile)

    @staticmethod
    def flattenJSON(y):
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '_')
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + '_')
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(y)
        return out

    def run(self):

        for t in self.paramTableDict:

            _tableName = t
            _fields = self.paramTableDict[t]['fields']
            _primaryKey = self.paramTableDict[t]['primaryKey']

            tableDefinition = self.createTableDefinition(
                _tableName, _fields, _primaryKey)
            self.createManifest(destination=tableDefinition.full_path + '.manifest',
                                pk=tableDefinition.table_def.pk,
                                incremental=self.paramIncremental)

            if _tableName == 'commissions':

                self.writerCommissions = self.createWriter(tableDefinition)
                logging.info("Created commissions table.")

            elif _tableName == 'commissions-items':

                self.writerItems = self.createWriter(tableDefinition)
                logging.info("Created commissions-items table.")

            else:

                logging.error("Unknown table definition received!")
                sys.exit(2)
