from recommendation_system import item_categories,unified_recommend,rules,menu_by_cat,menu_dict
from sql_conn import df


cart     = [113743,113710,113711,113712]

print("CART ITEMS: ")
for item in cart:
    print(menu_dict.get(item),"--->",item_categories.get(item))
recs     = unified_recommend(
    cart_items    = cart,
    rules         = rules,
    df            = df,
    menu_by_cat=menu_by_cat,customer_number="01005493632")
print("_"*30)
print("RECOMMENDATIONS: ")
print(recs)
for item in recs:
    print(menu_dict.get(item),"---->",item_categories.get(item))

# #output
# # CART ITEMS: 
# # Curly Fries ---> Fries
# # Jnash  ---> Junior style
# # WildEpic ---> Wild Style
# # WildBlaze ---> Wild Style
# # ______________________________
# # RECOMMENDATIONS: 
# # v7 cola ----> Drinks
# # Mega Drip ----> Side items
# # EXTRA Sauce ----> Side items

