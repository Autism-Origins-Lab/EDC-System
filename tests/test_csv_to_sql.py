import unittest
import sys
sys.path.insert(0, '../')

import csv_to_sql

class Test_VerifySpreadsheetAndReadToDataframe(unittest.TestCase):
    # ensures that a valid CSV file returns expected results
    def test_validcsvfile(self):
        csv_to_sql.filename = "testdata/DummyData.csv"
        self.assertTrue(csv_to_sql.upload())

if __name__ == "__main__":
    unittest.main()