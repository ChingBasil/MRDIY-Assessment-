## Transforming Data using SQL ##
~ Open DBeaver > Click Database > New Connection > MySQL. (Since i choosed to used MySQL)

~ In the SQL Editor, create your working database.

~ Take the raw dataset from excel_sample_data_de, sheet sql_test-raw.

~ Import the data into MySQL via DBeaver.

~ I have created a folder that contains all the nessesary SQL scripts to set up and run the requested transformations.

~ Create table sales_raw by running the "sales_raw" SQL script to get a raw dataset in MySQL.

~ Import data into "sales_raw" by right clicking it > choose excel_sample_data_de.xlsx, sheet sql_test-raw > Next > Finish.

~ Create a base table with profit by running the "sales_base" SQL script.

~ Compute monthly totals by category by running the "category_totals" SQL script.

~ Finally to join totals back to main table and compute contributions run the "sql_test_expected" SQL script.

~ To export the data, right click results > Export Data as an Excel file.

## Transforming Data using Python ##
~ Open VS Code > install pandas and openpyxl.

~ Open excel_sample_data_de in project directory.

~ Run "data_transform.py" located in folder "Python Script".

~ The output of the validation summary should be displayed. 

