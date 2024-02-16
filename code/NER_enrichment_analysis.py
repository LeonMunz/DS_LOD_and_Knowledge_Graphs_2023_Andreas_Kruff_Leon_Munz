import pandas as pd
import pickle
from itertools import chain
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
from fuzzywuzzy import fuzz
from bs4 import BeautifulSoup
from itertools import chain
from collections import Counter
import json
from itertools import islice


def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def apply_prepro_on_col(data, column):

    if type(column) == list:
        for json_obj in data:
            original_value = json_obj[column[0]]
            if original_value is None or len(original_value) == 0:
                json_obj[column[0]] = []
            else:
                cleaned_values = []
                for i in original_value:
                    cleaned_values.append({"keyword" : remove_html_tags(i["keyword"]), "score" : i["score"]})
                json_obj[column[0]] = cleaned_values
        return data

def calculate_intersection(df, field):
    fuzzy_percentage = []
    exact_match_percentage = []
    exact_not_included_in_entities = []
    fuzzy_not_included_in_entities = []
    for i, j in df.iterrows():
        entities = j[field]
        enriched_entities = j["Enriched_Entities"]
        fuzzy_intersection = [word for word in entities if
                              any(fuzz.ratio(word, entity) > 80 for entity in enriched_entities)]
        exact_match_intersection = [word for word in entities if
                                    any(fuzz.ratio(word, entity) >= 100 for entity in enriched_entities)]

        missing_entities_exact = [entity for entity in enriched_entities if
                                  all(fuzz.ratio(entity, word) < 100 for word in entities)]
        missing_entities_fuzzy = [entity for entity in enriched_entities if
                                  all(fuzz.ratio(entity, word) < 80 for word in entities)]
        exact_not_included_in_entities.append(missing_entities_exact)
        fuzzy_not_included_in_entities.append(missing_entities_fuzzy)

        if len(enriched_entities) > 0:
            fuzzy_match_perc = (len(fuzzy_intersection) / len(enriched_entities)) * 100
            exact_match_perc = (len(exact_match_intersection) / len(enriched_entities)) * 100
        else:
            fuzzy_match_perc = 0
            exact_match_perc = 0

        fuzzy_percentage.append(fuzzy_match_perc)
        exact_match_percentage.append(exact_match_perc)

    df["Fuzzy_match_percenatage"] = fuzzy_percentage
    df["Exact_match_percentage"] = exact_match_percentage

    print(
        f"Average percentage of intersection between field {field} and field Enriched Entities (using a fuzzy match of 80 %):",
        df["Fuzzy_match_percenatage"].mean(), " %")
    print(
        f"Average percentage of intersection between field {field} and field Enriched Entities (using an exact match):",
        df["Exact_match_percentage"].mean(), " %")

    flat_exact_not_included_in_entities = list(chain(*exact_not_included_in_entities))
    flat_fuzzy_not_included_in_entities = list(chain(*fuzzy_not_included_in_entities))

    word_counts_keywords_100 = Counter(flat_exact_not_included_in_entities)
    with open(f"../data/word_counts_{field}_100.json", 'w') as json_file:
        json.dump(word_counts_keywords_100, json_file)

    word_counts_keywords_80 = Counter(flat_fuzzy_not_included_in_entities)
    with open(f"../data/word_counts_{field}_80.json", 'w') as json_file:
        json.dump(word_counts_keywords_80, json_file)

    return df

def show_top_10_not_intersecting():
    path_list = ["../data/word_counts_keywords_100.json", "../data/word_counts_keywords_80.json", "../data/word_counts_mesh_100.json",
                 "../data/word_counts_mesh_80.json"]
    list_top10 = []
    for i in path_list:
        with open(i, "r") as json_file:
            loaded_word_counts = json.load(json_file)
            sorted_word_counts = dict(sorted(loaded_word_counts.items(), key=lambda item: item[1], reverse=True))
            top_10 = list(islice(sorted_word_counts.keys(), 10))
            list_top10.append(top_10)

    transposed_data_list = list(map(list, zip(*list_top10)))

    print(transposed_data_list)
    df = pd.DataFrame(transposed_data_list,
                      columns=["Words (keywords 100)", "Words (keywords 80)", "Words (mesh 100)", "Words (mesh 80)"])
    df.index = range(1, len(df) + 1)

    print(df.to_markdown())

# Reading the NER dataset
nerfile = open('../data/NER_data_MESH.pickle', 'rb')
ner = pickle.load(nerfile)

# Extract the entities from the dicts for further quantitative and qualitative analysis
aggregated_entity_sets = []
for i in ner:
    entity_sets_per_item = []
    for j in ["hasGene_GeneProduct", "hasCEL", "hasORGANISM","hasORGAN"]:
        entity_sets_per_item.append(i[j])
    aggregated_entity_sets.append({i["ID"] : list(set.union(*entity_sets_per_item))})

# Extracting and separating the keys and values for creating a pandas Dataframe for further analysis
keys = [list(d.keys())[0] for d in aggregated_entity_sets]
values = [list(map(str.lower, list(d.values())[0])) for d in aggregated_entity_sets]


enriched_entities_df = pd.DataFrame({'id': keys, 'Enriched_Entities': values})

# Reading the 5k dataset that was used as a  basis of this project
dbfile = open('../data/dataset_5k.pickle', 'rb')
db = pickle.load(dbfile)

# Cleaning the keyword strings from HTML tags
db = apply_prepro_on_col(db, ["keywords", "keyword"])

df_db = pd.DataFrame(db)

# Removing all unnecessary columns
columns_to_keep = ['id', 'keywords', 'mesh']
df_db = df_db.loc[:, df_db.columns.intersection(columns_to_keep)]

# Overwriting the columns in the dataframe with lists of the given lowercased entities
for i,j in df_db.iterrows():
    keywords_temp = []
    try:
        for k in j["keywords"]:
            keywords_temp.append(k["keyword"].lower())
    except:
        continue
    df_db.at[i, "keywords"] = keywords_temp

    mesh_temp = []
    for k in j["mesh"]:
        mesh_temp.append(k["descriptor_name"].lower())
    df_db.at[i,  "mesh"] = mesh_temp

# Merging the 5k dump df with the df with the enriched entites by the ID
# Inner join to filter the articles that have no abstract given
df_merge= df_db.merge(enriched_entities_df, on="id", how="inner")

# Calculating the amount of entities that are given for the underlying field for potential further analysis
df_merge['keywords_len'] = df_merge['keywords'].apply(lambda x: len(x) if isinstance(x, list) else 0)
df_merge['mesh_len'] = df_merge['mesh'].apply(lambda x: len(x) if isinstance(x, list) else 0)


df_merge = calculate_intersection(df_merge, "keywords")
df_merge = calculate_intersection(df_merge, "mesh")

show_top_10_not_intersecting()

count_no_keywords = 0
count_no_mesh = 0
count_no_keywords_no_enr= 0
count_no_mesh_no_enr= 0
article_ids_with_NER_entities =[]
article_ids_without_NER_entities = []
for i, j in df_merge.iterrows():
    if len(j["keywords"]) == 0 and len(j["Enriched_Entities"]) == 0:
        count_no_keywords_no_enr += 1
        article_ids_without_NER_entities.append(i)
    elif len(j["keywords"]) == 0 and len(j["Enriched_Entities"]) != 0:
        count_no_keywords += 1
        article_ids_with_NER_entities.append(i)
    elif len(j["mesh"]) == 0 and len(j["Enriched_Entities"]) == 0:
        count_no_mesh_no_enr +=1
        article_ids_without_NER_entities.append(i)

    elif len(j["mesh"]) == 0 and len(j["Enriched_Entities"]) != 0:
        count_no_mesh += 1
        article_ids_with_NER_entities.append(i)


print(count_no_keywords, "articles with no keywords given")
print(count_no_mesh, "articles with no meshterms given")
print(count_no_keywords_no_enr, "articles without keywords or enriched entites by Ner given")
print(count_no_mesh_no_enr, "articles without mesh or enriched entites by Ner given")

# Calculating the intersection between articles that have no mesh terms and no keywords but entities from NER
article_ids_with_NER_entities = list(set(article_ids_with_NER_entities))

# Calculating the intersection between articles that have no mesh terms and no keywords and no entities from NER
article_ids_without_NER_entities = list(set(article_ids_without_NER_entities))

print(len(article_ids_without_NER_entities), "Amount of articles that have no entities in keywords or mesh and could not been enriched by NER")
print(len(article_ids_with_NER_entities), "Amount of articles that have no entities in keywords or mesh but were enriched by NER")









