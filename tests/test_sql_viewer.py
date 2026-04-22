import unittest
import sys
import os
import pandas as pd
import sqlite3
sys.path.insert(0, '../')

import sql_viewer

class Test_GetSQLDatabase(unittest.TestCase):
    # setup for all tests
    @classmethod
    def setUpClass(cls):
        cls.data = {
            "Integer": [23423, 54235, 3432, 327489, 37284, 2910, 392048, 934820, 3498, 32984, 593, 48239, 498320, 39428, 34982, 23948, 95483],
            "Text": ["kajfklsd", "kdsfjk", "skdjfkl", "ksdfjldsa", "klsdjfk", "ksdjfl", "sjaflk", "skjdfla", "ksldjfklas", "kdjsfk", "dsjfkcx", "dkfjlx", "dkjflksw", "sdkjflw", "xcjvlk", "wejrlwk", "dskjfk"],
            "Date": ["4/2/26", "5/23/26", "12/4/26", "1/23/26", "5/24/26", "9/3/26", "2/3/26", "5/9/26", "9/21/26", "10/4/26", "1/19/26", "3/4/26", "5/12/26", "9/23/26", "8/27/26", "5/19/26", "11/18/26"],
            "Boolean": [True, False, False, True, True, True, False, True, False, False, False, True, False, False, True, False, True],
            "Decimal": [234.5231, 57238.3284, 4327.234, 51.234, 5.1234124, 723589.213478, 58.13844, 583218.324, 85.389124, 9.2314, 3932.32941, 4932.392, 931.32491, 493.24913, 439.23491, 0.34812, 3214.23432]
        }
        cls.df = pd.DataFrame(cls.data)
        cls.df['Date'] = pd.to_datetime(cls.df['Date'])
        cls.headers = {"Integer": "INTEGER", "Text": "TEXT", "Date": "DATETIME", "Boolean": "BOOLEAN", "Decimal": "FLOAT"}

        cls.connection = sqlite3.connect("databases/test.db")
        cls.df.to_sql("Testing123", cls.connection, if_exists="replace", index=False, dtype=cls.headers)

    # test getting a list of tables from a database
    def test_gettables(self):
        tables = sql_viewer.gettables("test.db")
        self.assertEqual(tables, ["Testing123"])

    # test getting table data
    def test_gettabledata(self):
        data = sql_viewer.gettabledata("test.db", "Testing123")
        data['Date'] = pd.to_datetime(data['Date'])
        for header in data.columns:
            for index in range(len(data[header])):
                self.assertTrue(data[header][index] == self.df[header][index])

    # clearing databases for tests
    @classmethod
    def tearDownClass(cls):
        cls.connection.execute("DROP TABLE IF EXISTS Testing123")
        cls.connection.close()

class Test_SortingData(unittest.TestCase):
    # setup for all tests
    @classmethod
    def setUpClass(cls):
        cls.data = {
            "Integer": [23423, 54235, 3432, 327489, 37284, 2910, 392048, 934820, 3498, 32984, 593, 48239, 498320, 39428, 34982, 23948, 95483],
            "Text": ["kajfklsd", "kdsfjk", "skdjfkl", "ksdfjldsa", "klsdjfk", "ksdjfl", "sjaflk", "skjdfla", "ksldjfklas", "kdjsfk", "dsjfkcx", "dkfjlx", "dkjflksw", "sdkjflw", "xcjvlk", "wejrlwk", "dskjfk"],
            "Date": ["4/2/26", "5/23/26", "12/4/26", "1/23/26", "5/24/26", "9/3/26", "2/3/26", "5/9/26", "9/21/26", "10/4/26", "1/19/26", "3/4/26", "5/12/26", "9/23/26", "8/27/26", "5/19/26", "11/18/26"],
            "Boolean": [True, False, False, True, True, True, False, True, False, False, False, True, False, False, True, False, True],
            "Decimal": [234.5231, 57238.3284, 4327.234, 51.234, 5.1234124, 723589.213478, 58.13844, 583218.324, 85.389124, 9.2314, 3932.32941, 4932.392, 931.32491, 493.24913, 439.23491, 0.34812, 3214.23432]
        }
        cls.df = pd.DataFrame(cls.data)
        cls.df['Date'] = pd.to_datetime(cls.df['Date'])
        cls.headers = {"Integer": "INTEGER", "Text": "TEXT", "Date": "DATETIME", "Boolean": "BOOLEAN", "Decimal": "FLOAT"}

        cls.connection = sqlite3.connect("databases/test.db")
        cls.df.to_sql("Testing123", cls.connection, if_exists="replace", index=False, dtype=cls.headers)

    # clearing databases for tests
    @classmethod
    def tearDownClass(cls):
        cls.connection.execute("DROP TABLE IF EXISTS Testing123")
        cls.connection.close()

if __name__ == "__main__":
    unittest.main()