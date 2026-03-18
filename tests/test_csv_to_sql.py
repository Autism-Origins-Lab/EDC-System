from . import csv_to_sql
import unittest

class Test_VerifySpreadsheetAndReadToDataframe(unittest.TestCase):
    # ensures that a valid CSV file returns expected results
    def test_validcsvfile(self):
        csv_to_sql.filename = "testdata/DummyData.csv"
        self.assertTrue(csv_to_sql.upload())

if __name__ == "__main__":
    unittest.main()