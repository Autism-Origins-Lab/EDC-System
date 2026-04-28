import unittest
import sys
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
        tables = sql_viewer.gettables("test")
        self.assertEqual(tables, ["Testing123"])

    # test getting table data
    def test_gettabledata(self):
        data = sql_viewer.gettabledata("test", "Testing123")
        data['Date'] = pd.to_datetime(data['Date'])
        for header in data.columns:
            for index in range(len(data[header])):
                self.assertEqual(data[header][index], self.df[header][index])

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
        cls.expected_ascending_df = cls.df.sort_values("Integer", ascending=True)
        cls.expected_ascending_decimal_df = cls.df.sort_values("Decimal", ascending=True)
        cls.expected_descending_df = cls.df.sort_values("Integer", ascending=False)

    # test flipping from ascending to descending back to ascending
    def test_flipSorting(self):
        actual_ascending = sql_viewer.sort("Integer", self.df)
        actual_descending = sql_viewer.sort("Integer", self.df)
        actual_reascending = sql_viewer.sort("Integer", self.df)
        for header in actual_ascending.columns:
            for index in range(len(actual_ascending[header])):
                self.assertEqual(self.expected_ascending_df[header][index], actual_ascending[header][index])
                self.assertEqual(self.expected_descending_df[header][index], actual_descending[header][index])
                self.assertEqual(self.expected_ascending_df[header][index], actual_reascending[header][index])

    # test not flipping from ascending to sorting by a different column back to ascending
    def test_notFlippingSorting(self):
        actual_ascending = sql_viewer.sort("Integer", self.df)
        actual_different = sql_viewer.sort("Decimal", self.df)
        actual_reascending = sql_viewer.sort("Integer", self.df)
        for header in actual_ascending.columns:
            for index in range(len(actual_ascending[header])):
                self.assertEqual(self.expected_ascending_df[header][index], actual_ascending[header][index])
                self.assertEqual(self.expected_ascending_decimal_df[header][index], actual_different[header][index])
                self.assertEqual(self.expected_ascending_df[header][index], actual_reascending[header][index])

class Test_FilteringData(unittest.TestCase):
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

    # test inclusion
    def test_include(self):
        expected_list = [327489, 2910]
        actual_list = sql_viewer.filter_table("Include", "Text", "ksd", self.df)["Integer"].to_list()
        self.assertEqual(expected_list, actual_list)

    # test exclusion
    def test_exclude(self):
        expected_list = [23423, 54235, 3432, 37284, 392048, 934820, 3498, 32984, 593, 48239, 498320, 39428, 34982, 23948, 95483]
        actual_list = sql_viewer.filter_table("Exclude", "Text", "ksd", self.df)["Integer"].to_list()
        self.assertEqual(expected_list, actual_list)

if __name__ == "__main__":
    unittest.main()