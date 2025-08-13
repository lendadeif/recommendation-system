import pyodbc
import pandas as pd
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-L7VUOTQG\\SQLEXPRESS;'
    'DATABASE=ResErp_DB;'
    'UID=sa;'
    'PWD=lendaalaa277'
)
query = """
SELECT 
    bill.Bill_ID,
    bill_d.item_ID,
    bill_d.QUANTITY,
    bill_d.PRICE,
    bill_d.Total AS ItemTotal,
    bill_d.ItemName,
    bill_d.ItemType,
    item.Scat_ID,
    cat.SCatName,
    bill.TotalDate,
    bill.CustomerMobileNo
FROM ResErp_DB.dbo.tab_Bill bill
JOIN ResErp_DB.dbo.tab_Bill_detail bill_d 
    ON bill.Bill_ID = bill_d.Bill_ID
JOIN ResErp_DB.dbo.tab_item item 
    ON bill_d.item_ID = item.item_ID
JOIN ResErp_DB.dbo.tab_SubCategory cat 
    ON item.Scat_ID = cat.Scat_ID
where bill_d.item_ID!=0 and bill_d.ItemType !=5;
"""
df = pd.read_sql_query(query, conn)
