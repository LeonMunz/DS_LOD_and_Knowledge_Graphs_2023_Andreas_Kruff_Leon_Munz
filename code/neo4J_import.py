from neo4j import GraphDatabase, RoutingControl
import pickle
import pandas as pd
from bs4 import BeautifulSoup
import json
import re

# Credentials for accessing the local Neo4J instance
URI = "neo4j://localhost:7999"
AUTH = ("neo4j", "password")

def data_import_and_prepro():
    dbfile = open('../data/dataset_5k.pickle', 'rb')
    db = pickle.load(dbfile)

    # Applying Tag removal for JSON file with 5000 dump for all fields of fields_to_filter
    fields_to_filter = ["display_name", "title", ["keywords", "keyword"]]
    for i in fields_to_filter:
        db = apply_prepro_on_col(db, i)

    # Applying aggregations for JSON file with 5000 dump for all fields of fields_to_aggregate

    fields_to_aggregate = [("cited_by_count", 5000),(["apc_paid", "value_usd"], 500)]
    for i in fields_to_aggregate:
        db = aggregate_value_fields(db,i[0] , step=i[1])

    # Import dataset with ID and corresponding Named Entities
    nerfile = open('../data/NER_data_MESH.pickle', 'rb')
    ner = pickle.load(nerfile)

    # Import additional author metadata
    with open("../data/author_data.json", 'r') as json_file:
        auth = json.load(json_file)

    # Import file with the ID and the Title for the referenced articles
    with open("../data/df_references.pkl", 'rb') as pickle_file:
        ref = pickle.load(pickle_file)

    # Filter HTML tags from titles
    ref = apply_prepro_on_col(ref, "title")

    return db, ner, auth, ref


def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

def replace_with_ranges(value, step=1000):
    return value // step * step

def find_and_return_value(json_list, search_key, search_value, return_key):

    for json_obj in json_list:

        if search_key in json_obj and json_obj[search_key] == search_value:
            return json_obj.get(return_key)
    return None

def apply_prepro_on_col(data, column):

    if type(column) == str:
        for json_obj in data:
            original_value = json_obj[column]

            if original_value is None or not isinstance(original_value, str):
                cleaned_title = None
            else:
                cleaned_title = remove_html_tags(original_value)
                if cleaned_title.isupper():
                    cleaned_title = to_title(cleaned_title)
            json_obj[column] = cleaned_title
        return data
    if type(column) == list:
        for json_obj in data:
            original_value = json_obj[column[0]]
            if original_value is None or len(original_value) == 0:
                json_obj[column[0]] = None
            else:
                cleaned_values = []
                for i in original_value:
                    cleaned_values.append({"keyword" : remove_html_tags(i["keyword"]), "score" : i["score"]})
                json_obj[column[0]] = cleaned_values
        return data


def to_title(string, excluded_words=None):
    if excluded_words is None:
        excluded_words = set(["a", "an", "and", "the", "for", "from", "in", "of", "to", "by", "that"])

    regex = re.compile("[a-zA-Z]+('[a-zA-Z]+)?")

    def title_case(match):
        word = match.group(0).lower()
        return word if word in excluded_words or word.upper() in excluded_words else word.capitalize()

    title_cased_string = regex.sub(title_case, string)
    return title_cased_string[0].upper() + title_cased_string[1:]

def aggregate_value_fields(data, column, step):
    if type(column) == str:
        for json_obj in data:
            original_count = json_obj[column]

            if original_count is None:
                json_obj[f"{column}_Agg"] = None
            else:
                range = replace_with_ranges(original_count, step=step)
                json_obj[f"{column}_Agg"] = "> " + str(range)
        return data
    if type(column) == list:
        for json_obj in data:
            original_count = json_obj[column[0]]

            if original_count is None:
                json_obj[f"{column[0]}_Agg"] = None
            else:
                range = replace_with_ranges(original_count[column[1]], step=step)
                json_obj[f"{column[0]}_Agg"] = "> " + str(range)
        return data


def add_entity_relations(driver, entity1, entity_1_type,entity_1_type_short, entity2, entity_2_type, entity_2_type_short, relation, type1, type2):
    driver.execute_query(
        f"MERGE ({entity_1_type_short}:{entity_1_type} {{{type1}: $entity1}}) "
        f"MERGE ({entity_2_type_short}:{entity_2_type} {{{type2}: $entity2}}) "
        f"MERGE ({entity_1_type_short})-[:{relation}]->({entity_2_type_short})",
        entity1=entity1, entity2=entity2, relation = relation, database_="neo4j",
    )

def add_entity_attribute(driver, entity1, entity_1_type,entity_1_type_short, entity2, type1, type2):
    driver.execute_query(
        f"MERGE ({entity_1_type_short}:{entity_1_type} {{{type1}: $entity1}}) "
        f"SET {entity_1_type_short}.{type2} = $entity2, {entity_1_type_short}.name = $entity1",
        entity1=entity1, entity2=entity2, database_="neo4j"

    )


def add_NER_to_Article(i, ner):
    for j in ner:
        if i["id"] == j["ID"]:
            if i["title"] is not None and isinstance(i["title"], str):
                if len(j["hasGene_GeneProduct"]) > 0:
                    for k in j["hasGene_GeneProduct"]:
                        add_entity_relations(driver, i["title"], "Title", "tit",
                                             k, "Gene", "G", "hasEntGene",
                                             type1="name", type2="name")
                if len(j["hasCEL"]) > 0:
                    for k in j["hasCEL"]:
                        add_entity_relations(driver, i["title"], "Title", "tit",
                                             k, "Cell", "C", "hasEntCell",
                                             type1="name", type2="name")
                if len(j["hasORGANISM"]) > 0:
                    for k in j["hasORGANISM"]:
                        add_entity_relations(driver, i["title"], "Title", "tit",
                                             k, "Organism", "Org", "hasEntOrganism",
                                             type1="name", type2="name")
                if len(j["hasORGAN"]) > 0:
                    for k in j["hasORGAN"]:
                        add_entity_relations(driver, i["title"], "Title", "tit",
                                             k, "Organ", "O", "hasEntOrgan",
                                             type1="name", type2="name")

def add_RefArt_to_Art(title,referenced_works ,db_references,direction):

    if (
           i["title"] is not None and isinstance(i["title"], str) and
           len(i["referenced_works"]) != 0
    ):
        for j in referenced_works:
            ref_title = find_and_return_value(db_references, "id", j, "title")
            if ref_title == None:
                continue
            else:
                if direction == "RefToArt":
                    add_entity_relations(driver, ref_title, "RefTitle", "Rtit", title, "Title", "tit","ReferencedBy", type1="name",type2="name")
                else:
                    add_entity_relations(driver, title, "Title", "tit",ref_title, "RefTitle", "Rtit", "ReferencedBy",type1="name", type2="name")

def add_Journal_to_Art(title, journal_name ):
    # OA status of Article and Journal
    if (
            journal_name is not None and isinstance(journal_name, str) and
            title is not None and isinstance(title, str)
    ):

        # Adds the Relation between Journal_name and article title as "PublishedIn"
        try:
            add_entity_relations(driver, title, "Title", "tit",
                                 journal_name, "journal_name", "jname", "PublishedIn",
                                 type1="name", type2="name")
        except:
            print(title, journal_name)

def add_OA_Attribute(title, OA_Attribute):
    if (
            i["locations"] is not None and
            j["is_oa"] is not None
    ):
        add_entity_attribute(driver, title, "Title", "tit",
                                 OA_Attribute, "name", "isOA")

def add_apc_paid_to_Art(title, value_usd_range,value_usd):

    # Adds PriceIn$ as Attribute to the Article title
    add_entity_attribute(driver, title, "Title", "tit", value_usd, "name", "PriceInUSD")

    add_entity_relations(driver, title, "Title", "tit", value_usd_range,
                         "Price_in_$", "Price", "ActualPricePaid", type1= "name", type2 ="name" )


def add_cite_count_to_Art(title, count_cite, count_cite_agg):

    add_entity_attribute(driver, title, "Title", "tit", count_cite, "name", "AmountCites")
    add_entity_relations(driver, title, "Title", "tit", count_cite_agg,
                             "Cites", "Cit", "CountOfCites", type1="name", type2="name")

def add_authors_to_Art(title, author_position, author_name):
    if author_position == "first":

        add_entity_relations(driver, author_name, "author",
                             "auth", title, "Title", "tit", "hasFirstAuthor", "name", "name")
    else:
        add_entity_relations(driver, author_name, "author",
                             "auth", title, "Title", "tit", "hasAuthorship", "name", "name")


if __name__ == "__main__":

    db, ner, auth, ref = data_import_and_prepro()

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()

    for i in db:
        add_NER_to_Article(i, ner)

        add_entity_attribute(driver, i["title"], "Title", "tit", i["doi"],"name", "hasDOI")

        add_RefArt_to_Art(i["title"], i["referenced_works"],ref, direction="RefToArt")
        if (
                i["title"] is not None and isinstance(i["title"], str) and
                i["apc_paid"] is not None and
                i["apc_paid_Agg"] is not None and isinstance(i["apc_paid_Agg"], str) and
                i["apc_paid"]["value_usd"] is not None and isinstance(i["apc_paid"]["value_usd"], int)

        ):
            add_apc_paid_to_Art(i["title"], i["apc_paid_Agg"],i["apc_paid"]["value_usd"])

        if (
                i["title"] is not None and isinstance(i["title"], str) and
                i["cited_by_count"] is not None and
                i["cited_by_count_Agg"] is not None and isinstance(i["cited_by_count_Agg"], str)
        ):
            add_cite_count_to_Art(i["title"], i["cited_by_count"], i["cited_by_count_Agg"])

        if (
                i["title"] is not None and isinstance(i["title"], str) and
                i["is_retracted"] is not None

        ):
            add_entity_attribute(driver, i["title"], "Title", "tit", i["is_retracted"], "name", "isRetracted")


        ## Add Keywords and Mesh words to Article
        if (
                i["title"] is not None and isinstance(i["title"], str) and
                i["keywords"] is not None

        ):
            for j in i["keywords"]:
                if j["score"] >= 0.7:
                    add_entity_relations(driver, i["title"], "Title", "tit", j["keyword"],
                                         "Keyword", "Key", "hasTopic", "name", "name")

        if (
                i["title"] is not None and isinstance(i["title"], str) and
                i["mesh"] is not None and len(i["mesh"]) > 0

        ):
            for j in i["mesh"]:
                if j["is_major_topic"]:
                    add_entity_relations(driver, i["title"], "Title", "tit", j["descriptor_name"],
                                         "Mesh", "Mesh", "hasMeshTopic", "name", "name")


        add_entity_attribute(driver, i["title"], "Title", "tit", i["type"],"name", "Type")
        if (
                i["primary_location"] is not None and
                i["primary_location"]["source"] is not None and
                i["primary_location"]["source"]["display_name"] is not None and
                i["primary_location"]["source"]["type"] is not None
        ):
            add_entity_attribute(driver, i["primary_location"]["source"]["display_name"], "journal_name", "jname", i["primary_location"]["source"]["type"] ,"name", "Type")


        # Add Entity for OpenAcess status like gold in relation to Article
        add_entity_relations(driver, i["title"], "Title", "tit", i["open_access"]["oa_status"], "OAstatus",
                             "OAstatus", "hasOAStatus","name", "name")

        # Add Article Language as Attribute to Article
        add_entity_attribute(driver, i["title"], "Title", "tit", i["language"],"name", "Language")

        # Add Publication as both attribute and entity to KG
        add_entity_relations(driver, i["title"], "Title", "tit", i["publication_year"], "pub_year",
                             "year", "hasPublicationYear", "name", "name")
        add_entity_attribute(driver, i["title"], "Title", "tit", i["publication_year"],"name", "PublicationYear")

        ## Add Organization relation to Journal
        if (
                i["primary_location"] is not None and i["primary_location"]["source"] is not None and
                i["primary_location"]["source"]["display_name"] is not None and isinstance(i["primary_location"]["source"]["display_name"], str) and
                i["title"] is not None and isinstance(i["title"], str)
        ):
            add_entity_relations(driver, i["primary_location"]["source"]["display_name"], "journal_name", "jname",
                                 i["primary_location"]["source"]["host_organization_name"], "Organization_name",
                                 "Org", "refersTo","name","name")

        # Add Author and First Author relation to Article
        for j in i["authorships"]:
            add_authors_to_Art(i["title"], j["author_position"], j["author"]["display_name"])

        for j in i["locations"]:


            if (
                    i["locations"] is not None and
                    j["source"] is not None and
                    j["source"]["display_name"] is not None and
                    j["is_oa"] is not None

            ):
                add_Journal_to_Art(i["title"], j["source"]["display_name"])
            add_OA_Attribute(i["title"], j["is_oa"])

    for i in auth:
        if (
                i["display_name"] is not None and isinstance(i["display_name"], str) and
                i["last_known_institution"] is not None and isinstance(i["last_known_institution"]["display_name"],
                                                                       str)
        ):
            add_entity_relations(driver, i["display_name"], "author", "auth",
                                 i["last_known_institution"]["display_name"], "Institution", "Inst", "WorksFor", "name",
                                 "name")

