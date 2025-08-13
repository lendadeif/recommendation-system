from flask import Flask, request, jsonify
import pandas as pd
from recommendation_system import unified_recommend, rules, df, menu_by_cat  # Assume you modularize your code

app = Flask(__name__)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    
    # Input Validation
    cart = data.get('cart_items', [])
    customer_number = data.get('customer_number', None)
    top_n = data.get('top_n', 3)

    try:
        recommendations = unified_recommend(
            cart_items=cart,
            rules=rules,
            df=df,
            menu_by_cat=menu_by_cat,
            customer_number=customer_number,
            top_n=top_n
        )
        return jsonify({"recommendations": recommendations})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

