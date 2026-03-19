import unittest
import sys
import os
import pandas as pd
sys.path.insert(0, '../')

import csv_to_sql

class Test_VerifySpreadsheetAndReadToDataframe(unittest.TestCase):
    # setup for all tests
    @classmethod
    def setUpClass(cls):
        data = {
            "Integer": [23423, 54235, 3432, 327489, 37284, 2910, 392048, 934820, 3498, 32984, 593, 48239, 498320, 39428, 34982, 23948, 95483],
            "Text": ["kajfklsd", "kdsfjk", "skdjfkl", "ksdfjldsa", "klsdjfk", "ksdjfl", "sjaflk", "skjdfla", "ksldjfklas", "kdjsfk", "dsjfkcx", "dkfjlx", "dkjflksw", "sdkjflw", "xcjvlk", "wejrlwk", "dskjfk"],
            "Date": ["4/2/26", "5/23/26", "12/4/26", "1/23/26", "5/24/26", "9/3/26", "2/3/26", "5/9/26", "9/21/26", "10/4/26", "1/19/26", "3/4/26", "5/12/26", "9/23/26", "8/27/26", "5/19/26", "11/18/26"],
            "Boolean": [1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1],
            "Decimal": [234.5231, 57238.3284, 4327.234, 51.234, 5.1234124, 723589.213478, 58.13844, 583218.324, 85.389124, 9.2314, 3932.32941, 4932.392, 931.32491, 493.24913, 439.23491, 0.34812, 3214.23432]
        }
        cls.csvdata = pd.DataFrame(data)
        cls.xlsxdata = pd.DataFrame(data)
        cls.xlsxdata['Date'] = pd.to_datetime(cls.xlsxdata['Date'])
        cls.xlsxdata['Boolean'] = cls.xlsxdata['Boolean'].astype('bool')

    # ensures that a valid CSV file returns expected results
    def test_validcsvfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "DummyData.csv")
        outcome = csv_to_sql.verifyfilename()
        self.assertTrue(outcome)
        for header in self.csvdata.columns:
            for index in range(len(self.csvdata[header])):
                print("Testing equality of {0}, {1}".format(csv_to_sql.dataframe[header][index], self.csvdata[header][index]))
                self.assertTrue(csv_to_sql.dataframe[header][index] == self.csvdata[header][index])
    
    # ensures that a valid Excel file returns expected results
    def test_validxlsxfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "DummyData.xlsx")
        outcome = csv_to_sql.verifyfilename()
        self.assertTrue(outcome)
        for header in self.xlsxdata.columns:
            for index in range(len(self.xlsxdata[header])):
                print("Testing equality of {0}, {1}".format(csv_to_sql.dataframe[header][index], self.xlsxdata[header][index]))
                self.assertTrue(csv_to_sql.dataframe[header][index] == self.xlsxdata[header][index])

if __name__ == "__main__":
    unittest.main()