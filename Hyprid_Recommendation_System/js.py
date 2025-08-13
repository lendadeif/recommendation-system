# recommendation.py
import sys
import json
from recommendation_system import item_categories,unified_recommend,rules,menu_by_cat,menu_dict
from sql_conn import df

test_json = '''
{
    "cart_items": [113743,113710,113711,113712],
    "customer_number":"01005493632"
}
'''
if __name__ == "__main__":
    # Read input from command line
    input_data = json.loads(test_json)
    
    # Call your function with the parameters
    results = unified_recommend(
    cart_items    = input_data["cart_items"],
    rules         = rules,
    df            = df,
    menu_by_cat=menu_by_cat,customer_number=input_data["customer_number"])
        # add other parameters you need
    
    
    # Print results as JSON so C# can read it
    print(json.dumps(results))