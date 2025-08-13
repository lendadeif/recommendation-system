# LIBRARIES______________
import pandas as pd
from datetime import datetime
from collections import defaultdict
from scipy.stats import zscore
from sklearn.metrics.pairwise import cosine_similarity
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from sql_conn import df
# DATABASE CONNECTION___________


# SYSYEM__________________________________________
# _________PREPROCESSING__________________
df['Hour'] = df['TotalDate'].dt.hour
item_categories = dict(zip(df['item_ID'], df['SCatName']))
menu_by_cat = df.groupby('SCatName')['item_ID'].apply(list).to_dict()
menu_ids = df['item_ID'].unique().tolist()
df['SCatName'] = df['SCatName'].astype('category')
menu_dict = dict(zip(df["item_ID"], df["ItemName"]))
#  ______Association Rules_______
transactions = df.groupby('Bill_ID')['item_ID'].apply(list).tolist()
te = TransactionEncoder().fit(transactions)
df_trans = pd.DataFrame(te.transform(transactions), columns=te.columns_)

freq_itemsets = apriori(df_trans, min_support=0.002, use_colnames=True)
rules = association_rules(freq_itemsets, metric="lift", min_threshold=1)
rules = rules[
    (rules['confidence'] > 0.15) &
    (rules['lift'] > 1.05) &
    (rules['antecedents'].apply(len) <= 2)
].drop_duplicates(subset=['antecedents', 'consequents']).reset_index(drop=True)

item_list = df_trans.columns.tolist()
item_to_index = {item: idx for idx, item in enumerate(item_list)}
item_vectors = df_trans.T.values

# ___________ Period ___________________


def get_period(hour):
    if 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 24:
        return 'evening'
    else:
        return 'night'


df['period'] = df['Hour'].apply(get_period)
df['period'] = df['period'].astype('category')

periodly_counts = df.groupby(
    ['period', 'item_ID'], observed=True).size().unstack(fill_value=0)
periodly_z = periodly_counts.apply(zscore, axis=1).fillna(0)

# COLABORATIVE FILTERING _____________________


def get_similar_customers(customer_id, sim_matrix, top_n=5):
    if customer_id not in sim_matrix.index:
        return []
    sims = sim_matrix.loc[customer_id].drop(customer_id)
    return sims.sort_values(ascending=False).head(top_n).index.tolist()


def get_cf_recommendations(customer_id, user_item_matrix, sim_matrix, top_n=5):
    similar_customers = get_similar_customers(customer_id, sim_matrix)
    if not similar_customers:
        return pd.Series(dtype=float)
    neighbor_matrix = user_item_matrix.loc[similar_customers]
    scores = neighbor_matrix.sum().sort_values(ascending=False)
    already_bought = user_item_matrix.loc[customer_id]
    scores = scores[already_bought == 0]
    return scores.head(top_n)


# NOW TIME
current_period = get_period(datetime.now().hour)


def unified_recommend(cart_items, rules, df, menu_by_cat, category_synergy=None,
                      top_n=3, time_weight=0.3, synergy_weight=0.6, rule_weight=0.5, boost_weight=0.2,
                      customer_number=None, cf_weight=1.2):

    cart_set = set(cart_items)

    # COLABORATIVE_________________
    user_item_matrix = df.pivot_table(
        index='CustomerMobileNo',
        columns='item_ID',
        values='QUANTITY',
        aggfunc='count'
    ).fillna(0)

    customer_sim = pd.DataFrame(
        cosine_similarity(user_item_matrix),
        index=user_item_matrix.index,
        columns=user_item_matrix.index
    )

    if customer_number and customer_number in user_item_matrix.index:
        cf_scores = get_cf_recommendations(
            customer_number, user_item_matrix, customer_sim, top_n=top_n * 2)
        cf_scores = cf_scores.rename("cf_score")
    else:
        cf_scores = pd.Series(dtype=float)

    # RULE BASED_______________________
    rule_scores = defaultdict(float)
    for _, rule in rules.iterrows():
        if rule['antecedents'] & cart_set:
            for item in rule['consequents']:
                if item not in cart_set:
                    rule_scores[item] += rule['confidence'] * \
                        rule['lift'] * rule_weight
    # TIME BASED _________________
    time_df = (
        df[df['period'] == current_period]
        .groupby('item_ID').size()
        .rename('time_score')
    )
    # CATEGORIES RALATIONS_______
    synergy_scores = pd.Series(dtype=float)
    if category_synergy:
        cart_cats = df[df['item_ID'].isin(cart_set)]['SCatName'].unique()
        related_cats = set()
        for cat in cart_cats:
            related_cats.update(category_synergy.get(cat, []))
        synergy_items = df[df['SCatName'].isin(related_cats)]
        synergy_scores = synergy_items.groupby(
            'item_ID').size().rename('synergy_score').div(10)

    # UNSOLD ITEMS_________________
    sales_counts = df['item_ID'].value_counts()
    low_selling_threshold = sales_counts.quantile(0.25)
    low_selling_items = sales_counts[sales_counts <
                                     low_selling_threshold].index

    # INTEGRATE ALL SCORES______________
    all_scores = pd.Series(rule_scores).to_frame('rule_score')
    all_scores['time_score'] = time_df
    all_scores['synergy_score'] = synergy_scores
    all_scores['low_selling_boost'] = all_scores.index.isin(
        low_selling_items).astype(float)
    all_scores['cf_score'] = cf_scores

    all_scores = all_scores.fillna(0)
    # NORMALIZATION_____________

    def min_max_normalize(series):
        if series.max() == series.min():
            return pd.Series(0, index=series.index)
        return (series - series.min()) / (series.max() - series.min())

    for col in ['rule_score', 'time_score', 'synergy_score', 'low_selling_boost', 'cf_score']:
        all_scores[col] = min_max_normalize(all_scores[col])

    all_scores['total_score'] = (
        all_scores['rule_score'] * rule_weight +
        all_scores['time_score'] * time_weight +
        all_scores['synergy_score'] * synergy_weight +
        all_scores['cf_score'] * cf_weight
    )

    all_scores = all_scores[~all_scores.index.isin(cart_set)]
    recommended = all_scores.sort_values(
        'total_score', ascending=False).head(top_n).index.tolist()
    # FALLBACK_______________
    if len(recommended) < top_n:

        # Fallback: Recommend best sellers *for the current period only*
        fallback = (
            df[df['period'] == current_period]
            .groupby('item_ID')
            .size()
            .sort_values(ascending=False)
            .index.difference(cart_set)
            .difference(recommended)
            .tolist()
        )
        if len(recommended) + len(fallback) >= top_n:
            return recommended
        recommended += fallback[:top_n - len(recommended)]

        # fallback = []
        for items in menu_by_cat.values():
            for item in items:
                if item not in cart_set and item not in recommended and item not in fallback:
                    fallback.append(item)
                if len(recommended) + len(fallback) >= top_n:
                    break
            if len(recommended) + len(fallback) >= top_n:
                break
        recommended += fallback[:top_n - len(recommended)]

    return recommended
