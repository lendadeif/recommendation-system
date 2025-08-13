# transactions = df.groupby("Bill_ID")['Item'].apply(set).tolist()
# cleaned_transactions = [
#     [item for item in trans if item not in [None, '']] for trans in transactions]

# item_sets = pd.Series(transactions).explode().value_counts()
# items = item_sets.index.tolist()

# item_categories = df[['Item', 'Category']].drop_duplicates().set_index('Item')[
#     'Category'].to_dict()


# def best_match(item, candidates, threshold=80):
#     match = process.extractOne(
#         item, candidates,
#         scorer=fuzz.token_sort_ratio,
#         score_cutoff=threshold
#     )
#     return match[0] if match else None


# def extract_notes(txt):
#     irrelevant_patterns = [
#         r'delivery order difference', r'maxi cola difference', r'regular & spicy',
#         r'still have', r'with order', r'cup with order', r'with delivery',
#     ]
#     note_patterns = [
#         r'without [\w\s]+', r'no [\w\s]+', r'same but with [\w\s]+',
#         r'replace it with [\w\s]+', r'topped with [\w\s]+', r'top with [\w\s]+',
#         r'with extra [\w\s]+', r'with [\w\s]+', r'extra [\w\s]+', r'add [\w\s]+',
#         r'for my [\w\s]+', r'dont add [\w\s]+', r'do not add [\w\s]+',
#         r'not add [\w\s]+', r'no extra [\w\s]+', r'without extra [\w\s]+',
#         r'instead [\w\s]+', r'[\w\s]+ instead of [\w\s]+', r'only [\w\s]+',
#         r'[\w\s]+ only', r'on top [\w\s]+', r'divide [\w\s]+', r'split [\w\s]+',
#         r'full [\w\s]+', r'half [\w\s]+', r'non [\w\s]+', r'not [\w\s]+',
#         r'make it [\w\s]+', r'don\'t [\w\s]+', r'you [\w\s]+',
#         r'in [\w\s]+', r'^i [\w\s]+', r'combo [\w\s]+',
#     ]
#     note_txt = []
#     for pattern in irrelevant_patterns + note_patterns:
#         matches = re.findall(pattern, txt)
#         for match in matches:
#             note_txt.append(match.strip())
#             txt = txt.replace(match, "")
#     cleaned = re.sub(r'\s+', ' ', txt).strip()
#     return cleaned, note_txt


# def clean(order):
#     order = order.lower().strip()
#     order = re.sub(r"[^a-z0-9\s]", '', order)
#     order = re.sub(r"\s+", ' ', order)
#     order = re.sub(r"\band\b", '', order)
#     order, _ = extract_notes(order)
#     if order not in items:
#         order = best_match(order, items, threshold=80)
#     return order


# te = TransactionEncoder()
# te_ary = te.fit(cleaned_transactions).transform(cleaned_transactions)
# df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

# # Apriori
# frequent_itemsets = apriori(df_encoded, min_support=0.02, use_colnames=True)
# rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)
# rules = rules[
#     (rules['confidence'] > 0.5) &
#     (rules['lift'] > 1.2) &
#     (rules['antecedents'].apply(len) <= 2)  # Prefer shorter antecedents
# ]


# def get_recommendations(cart_items, top_n=5):
#     cart_items = [clean(item) for item in cart_items if item]
#     recommended = defaultdict(list)

#     for item in cart_items:
#         matched = rules[rules['antecedents'].apply(lambda x: item in x)]
#         for _, row in matched.iterrows():
#             for consequent in row['consequents']:
#                 cat = item_categories.get(consequent)
#                 if cat and consequent not in cart_items and consequent not in recommended[cat]:
#                     recommended[cat].append(consequent)

#     # Add fallback top sellers
#     all_recommended = [item for sublist in recommended.values()
#                        for item in sublist]
#     if len(all_recommended) < top_n:
#         top_sellers = item_sets[~item_sets.index.isin(
#             cart_items + all_recommended)].head(top_n).index
#         for item in top_sellers:
#             cat = item_categories.get(item)
#             if cat and item not in recommended[cat]:
#                 recommended[cat].append(item)

#     # Return as flat sorted list
#     final = []
#     for cat in ['main', 'side', 'drink', 'sauce']:
#         final.extend(recommended.get(cat, []))
#     return final[:top_n]


transactions = df.groupby("Bill_ID")['item_ID'].apply(set).tolist()
cleaned_transactions = [
    [item for item in trans if item not in [None, '']] for trans in transactions]

item_sets = pd.Series(transactions).explode().value_counts()
items = item_sets.index.tolist()

item_categories = df[['item_ID', 'Category']].drop_duplicates().set_index('item_ID')[
    'Category'].to_dict()


def deduplicate_rules(rules_df):
    rules_df['antecedents_str'] = rules_df['antecedents'].apply(
        lambda x: tuple(sorted(x)))
    rules_df['consequents_str'] = rules_df['consequents'].apply(
        lambda x: tuple(sorted(x)))

    deduped = rules_df.drop_duplicates(
        subset=['antecedents_str', 'consequents_str'])

    deduped = deduped.drop(columns=['antecedents_str', 'consequents_str'])

    return deduped.reset_index(drop=True)


te = TransactionEncoder()
te_ary = te.fit(cleaned_transactions).transform(cleaned_transactions)
df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

# Apriori
frequent_itemsets = apriori(df_encoded, min_support=0.02, use_colnames=True)
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)
rules = rules[
    (rules['confidence'] > 0.5) &
    (rules['lift'] > 1.2) &
    (rules['antecedents'].apply(len) <= 2)
]
rules = deduplicate_rules(rules)


def get_recommendations(cart_items, top_n=5):

    cart_items_cleaned = [item for item in cart_items if item]
    recommended = defaultdict(list)

    cart_set = set(cart_items_cleaned)
    if not cart_items_cleaned:
        for cat in ['main', 'side', 'drink', 'sauce']:
            top_items = df[df['Category'] ==
                           cat]['item_ID'].value_counts().index.tolist()
            for item in top_items:
                if item not in cart_set and item not in recommended[cat]:
                    recommended[cat].append(item)
                if len([x for sublist in recommended.values() for x in sublist]) >= top_n:
                    break
            if len([x for sublist in recommended.values() for x in sublist]) >= top_n:
                break
    else:

        for _, rule in rules.sort_values(['lift', 'confidence'], ascending=False).iterrows():
            antecedents_cleaned = set([rule['antecedents']])
            consequent = next(iter(rule['consequents']))

            if antecedents_cleaned.issubset(cart_set):
                cat = item_categories.get(consequent)
                if cat and consequent not in cart_set and consequent not in recommended[cat]:
                    recommended[cat].append(consequent)
                    if len([x for sublist in recommended.values() for x in sublist]) >= top_n:
                        break

    if len([x for sublist in recommended.values() for x in sublist]) < top_n:
        for cat in ['main', 'side', 'drink', 'sauce']:
            top_items = df[df['Category'] ==
                           cat]['item_ID'].value_counts().index.tolist()
            for item in top_items:
                if item not in cart_set and item not in recommended[cat]:
                    recommended[cat].append(item)
                if len([x for sublist in recommended.values() for x in sublist]) >= top_n:
                    break

    def flatten_recommendations(recommended, top_n=3):
        flat, seen = [], set()
        for cat in ['main', 'side', 'drink', 'sauce']:

            for item in recommended.get(cat, []):
                if item not in seen:
                    flat.append(item)
                    seen.add(item)
        return flat[:top_n]

    return flatten_recommendations(recommended, top_n)


df = pd.read_csv("cleaned_orders_with_ids.csv")
dictionary = dict(zip(df["item_ID"], df["Item"]))

cart = ['buffalo', 'cheddar sauce', 'vcola']
recommendations = get_recommendations(cart)
print("Cart:", cart)
rec = [dictionary.get(item, item) for item in recommendations]
print("Recommendations:", rec)

cart = ['buffalo', 'cheddar sauce', 'vcola']
recommendations = get_recommendations(cart)
print("Cart:", cart)
rec = [dictionary.get(item, item) for item in recommendations]
print("Recommendations:", rec)
