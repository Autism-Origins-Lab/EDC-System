import unittest
import sys
import os
import pandas as pd
import sqlite3
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
            "Boolean": [True, False, False, True, True, True, False, True, False, False, False, True, False, False, True, False, True],
            "Decimal": [234.5231, 57238.3284, 4327.234, 51.234, 5.1234124, 723589.213478, 58.13844, 583218.324, 85.389124, 9.2314, 3932.32941, 4932.392, 931.32491, 493.24913, 439.23491, 0.34812, 3214.23432]
        }
        cls.csvdata = pd.DataFrame(data)
        cls.xlsxdata = pd.DataFrame(data)
        cls.xlsxdata['Date'] = pd.to_datetime(cls.xlsxdata['Date'])

    # ensures that a valid CSV file returns expected results
    def test_validcsvfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "DummyData.csv")
        (outcome, title, message) = csv_to_sql.verifyfilename()
        self.assertFalse(outcome)
        for header in self.csvdata.columns:
            for index in range(len(self.csvdata[header])):
                self.assertTrue(csv_to_sql.dataframe[header][index] == self.csvdata[header][index])
    
    # ensures that a valid Excel file returns expected results
    def test_validxlsxfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "DummyData.xlsx")
        (outcome, title, message) = csv_to_sql.verifyfilename()
        self.assertFalse(outcome)
        for header in self.xlsxdata.columns:
            for index in range(len(self.xlsxdata[header])):
                self.assertTrue(csv_to_sql.dataframe[header][index] == self.xlsxdata[header][index])

    # ensures that if a file doesn't exist, an error returns
    def test_missingcsvfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "FakeFile.csv")
        (outcome, title, message) = csv_to_sql.verifyfilename()
        self.assertTrue(outcome)
        self.assertEqual(title, "Error: Invalid File")
        self.assertEqual(message, "File selected cannot be read.")

    def test_missingxlsxfile(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "FakeFile.xlsx")
        (outcome, title, message) = csv_to_sql.verifyfilename()
        self.assertTrue(outcome)
        self.assertEqual(title, "Error: Invalid File")
        self.assertEqual(message, "File selected cannot be read.")
    
    # ensures that if a file does not end with .csv or .xlsx, an error returns
    def test_badfilename(self):
        csv_to_sql.filename = os.path.join(os.path.dirname(__file__), "testdata", "Test.pdf")
        (outcome, title, message) = csv_to_sql.verifyfilename()
        self.assertTrue(outcome)
        self.assertEqual(title, "Error: Wrong Filetype")
        self.assertEqual(message, "File selected must either end with either .csv or .xlsx.")

class Test_ColumnConversions(unittest.TestCase):
    # setup for all tests
    @classmethod
    def setUpClass(cls):
        data = {
            "Integer": [23423, 54235, 3432, 327489, 37284, 2910, 392048, 934820, 3498, 32984, 593, 48239, 498320, 39428, 34982, 23948, 95483],
            "Text": ["kajfklsd", "kdsfjk", "skdjfkl", "ksdfjldsa", "klsdjfk", "ksdjfl", "sjaflk", "skjdfla", "ksldjfklas", "kdjsfk", "dsjfkcx", "dkfjlx", "dkjflksw", "sdkjflw", "xcjvlk", "wejrlwk", "dskjfk"],
            "Date": ["4/2/26", "5/23/26", "12/4/26", "1/23/26", "5/24/26", "9/3/26", "2/3/26", "5/9/26", "9/21/26", "10/4/26", "1/19/26", "3/4/26", "5/12/26", "9/23/26", "8/27/26", "5/19/26", "11/18/26"],
            "Boolean": [True, False, False, True, True, True, False, True, False, False, False, True, False, False, True, False, True],
            "Decimal": [234.5231, 57238.3284, 4327.234, 51.234, 5.1234124, 723589.213478, 58.13844, 583218.324, 85.389124, 9.2314, 3932.32941, 4932.392, 931.32491, 493.24913, 439.23491, 0.34812, 3214.23432]
        }
        cls.csvdata = pd.DataFrame(data)
        cls.xlsxdata = pd.DataFrame(data)
        cls.xlsxdata['Date'] = pd.to_datetime(cls.xlsxdata['Date'])

    # tests conversions to integer are behaving as expected
    def test_inttoint(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Integer")
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_floattoint(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Decimal")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Float Converted To Integer")
    
    def test_datetimetoint(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Date")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Date/Time Converted To Integer")

    def test_booleantoint_withconversion(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Boolean", boolean_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")

    def test_booleantoint_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Boolean", boolean_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Boolean Converted To Integer")
    
    def test_stringtoint(self):
        (error, title, message) = csv_to_sql.verify_int_column(self.xlsxdata, "Text")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Text Converted To Integer")
    
    # tests conversions to float are behaving as expected
    def test_floattofloat(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Decimal")
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_inttofloat_withconversion(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Integer", int_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")

    def test_inttofloat_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Integer", int_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Integer Converted To Decimal")
    
    def test_datetimetofloat(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Date")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Date/Time Converted To Decimal")
    
    def test_booleantofloat_withconversion(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Boolean", boolean_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_booleantofloat_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Boolean", boolean_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Boolean Converted To Decimal")
    
    def test_stringtofloat(self):
        (error, title, message) = csv_to_sql.verify_float_column(self.xlsxdata, "Text")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Text Converted To Decimal")
    
    # tests conversions to datetime are behaving as expected
    def test_datetimetodatetime(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Date")
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_inttodatetime(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Integer")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Integer Converted To Date/Time")
    
    def test_floattodatetime(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Decimal")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Float Converted To Date/Time")
    
    def test_booleantodatetime(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Boolean")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Boolean Converted To Date/Time")
    
    def test_stringtodatetime_withconversion(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.csvdata, "Date", string_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")

    def test_stringtodatetime_failedconversion(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Text", string_conversion=True)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Text Cannot Be Converted To Date/Time")
    
    def test_stringtodatetime_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_datetime_column(self.xlsxdata, "Text", string_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Text Converted To Date/Time")
    
    # tests conversions to boolean are behaving as expected
    def test_booleantoboolean(self):
        (error, title, message) = csv_to_sql.verify_boolean_column(self.xlsxdata, "Boolean")
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_inttoboolean(self):
        (error, title, message) = csv_to_sql.verify_boolean_column(self.xlsxdata, "Integer")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Integer Converted To Boolean")

    def test_floattoboolean(self):
        (error, title, message) = csv_to_sql.verify_boolean_column(self.xlsxdata, "Decimal")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Float Converted To Boolean")
    
    def test_datetimetoboolean(self):
        (error, title, message) = csv_to_sql.verify_boolean_column(self.xlsxdata, "Date")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Date/Time Converted To Boolean")
    
    def test_stringtoboolean(self):
        (error, title, message) = csv_to_sql.verify_boolean_column(self.xlsxdata, "Text")
        self.assertTrue(error)
        self.assertEqual(title, "Error: Text Converted To Boolean")
    
    # tests conversions to text are behaving as expected
    def test_stringtostring(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Text")
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")

    def test_inttostring_withconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Integer", int_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_inttostring_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Integer", int_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Integer Converted To Text")
    
    def test_floattostring_withconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Decimal", float_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_floattostring_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Decimal", float_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Float Converted To Text")
    
    def test_datetimetostring_withconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Date", datetime_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_datetimetostring_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Date", datetime_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Date/Time Converted To Text")
    
    def test_booleantostring_withconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Boolean", boolean_conversion=True)
        self.assertFalse(error)
        self.assertEqual(title, "No Error Found")
    
    def test_booleantostring_withoutconversion(self):
        (error, title, message) = csv_to_sql.verify_text_column(self.xlsxdata, "Boolean", boolean_conversion=False)
        self.assertTrue(error)
        self.assertEqual(title, "Error: Boolean Converted To Text")

class Test_CreateSQLDatabase(unittest.TestCase):
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
        cls.csvdata = pd.DataFrame(cls.data)
        cls.xlsxdata = pd.DataFrame(cls.data)
        cls.xlsxdata['Date'] = pd.to_datetime(cls.xlsxdata['Date'])
        cls.headers = {"Integer": "INTEGER", "Text": "TEXT", "Date": "DATETIME", "Boolean": "BOOLEAN", "Decimal": "FLOAT"}
    
    # test creating sql database
    def test_createdb(self):
        csv_to_sql.create_sql_db(self.xlsxdata, self.headers, "Testing123", "test", True)
        connection = sqlite3.connect("databases/test.db")

        result = connection.execute("SELECT Integer FROM Testing123")
        intlist = result.fetchall()
        intlist = [x[0] for x in intlist]
        self.assertEqual(intlist, self.data["Integer"])

        result = connection.execute("SELECT Text FROM Testing123")
        stringlist = result.fetchall()
        stringlist = [x[0] for x in stringlist]
        self.assertEqual(stringlist, self.data["Text"])

        result = connection.execute("SELECT Date FROM Testing123")
        datetimelist = result.fetchall()
        datetimelist = [x[0] for x in datetimelist]
        actualdatelist = [str(pd.to_datetime(x)) for x in self.data["Date"]]
        self.assertEqual(datetimelist, actualdatelist)

        result = connection.execute("SELECT Boolean FROM Testing123")
        booleanlist = result.fetchall()
        booleanlist = [x[0] for x in booleanlist]
        self.assertEqual(booleanlist, self.data["Boolean"])

        result = connection.execute("SELECT Decimal FROM Testing123")
        floatlist = result.fetchall()
        floatlist = [x[0] for x in floatlist]
        self.assertEqual(floatlist, self.data["Decimal"])

        connection.execute("DROP TABLE IF EXISTS Testing123")
        connection.close()
    
    # test adding to sql database
    def test_addtodb(self):
        csv_to_sql.create_sql_db(self.xlsxdata, self.headers, "Testing123", "test", True)
        csv_to_sql.create_sql_db(self.xlsxdata, self.headers, "Testing123", "test", False)
        connection = sqlite3.connect("databases/test.db")

        result = connection.execute("SELECT Integer FROM Testing123")
        intlist = result.fetchall()
        intlist = [x[0] for x in intlist]
        self.assertEqual(intlist, self.data["Integer"] + self.data["Integer"])

        result = connection.execute("SELECT Text FROM Testing123")
        stringlist = result.fetchall()
        stringlist = [x[0] for x in stringlist]
        self.assertEqual(stringlist, self.data["Text"] + self.data["Text"])

        result = connection.execute("SELECT Date FROM Testing123")
        datetimelist = result.fetchall()
        datetimelist = [x[0] for x in datetimelist]
        actualdatelist = [str(pd.to_datetime(x)) for x in self.data["Date"]]
        self.assertEqual(datetimelist, actualdatelist + actualdatelist)

        result = connection.execute("SELECT Boolean FROM Testing123")
        booleanlist = result.fetchall()
        booleanlist = [x[0] for x in booleanlist]
        self.assertEqual(booleanlist, self.data["Boolean"] + self.data["Boolean"])

        result = connection.execute("SELECT Decimal FROM Testing123")
        floatlist = result.fetchall()
        floatlist = [x[0] for x in floatlist]
        self.assertEqual(floatlist, self.data["Decimal"] + self.data["Decimal"])

        connection.execute("DROP TABLE IF EXISTS Testing123")
        connection.close()

    # test rewriting to sql database
    def test_rewritetodb(self):
        csv_to_sql.create_sql_db(self.xlsxdata, self.headers, "Testing123", "test", True)
        csv_to_sql.create_sql_db(self.xlsxdata, self.headers, "Testing123", "test", True)
        connection = sqlite3.connect("databases/test.db")

        result = connection.execute("SELECT Integer FROM Testing123")
        intlist = result.fetchall()
        intlist = [x[0] for x in intlist]
        self.assertEqual(intlist, self.data["Integer"])

        result = connection.execute("SELECT Text FROM Testing123")
        stringlist = result.fetchall()
        stringlist = [x[0] for x in stringlist]
        self.assertEqual(stringlist, self.data["Text"])

        result = connection.execute("SELECT Date FROM Testing123")
        datetimelist = result.fetchall()
        datetimelist = [x[0] for x in datetimelist]
        actualdatelist = [str(pd.to_datetime(x)) for x in self.data["Date"]]
        self.assertEqual(datetimelist, actualdatelist)

        result = connection.execute("SELECT Boolean FROM Testing123")
        booleanlist = result.fetchall()
        booleanlist = [x[0] for x in booleanlist]
        self.assertEqual(booleanlist, self.data["Boolean"])

        result = connection.execute("SELECT Decimal FROM Testing123")
        floatlist = result.fetchall()
        floatlist = [x[0] for x in floatlist]
        self.assertEqual(floatlist, self.data["Decimal"])

        connection.execute("DROP TABLE IF EXISTS Testing123")
        connection.close()

if __name__ == "__main__":
    unittest.main()