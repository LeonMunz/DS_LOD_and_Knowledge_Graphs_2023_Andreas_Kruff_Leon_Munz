import json
import pickle

dbfile = open('../data/dataset_5k.pickle', 'rb')
db = pickle.load(dbfile)

from bs4 import BeautifulSoup

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

for json_obj in db:
    original_title = json_obj["title"]
    if original_title is None or not isinstance(original_title, str):
        cleaned_title = "title not given"
    else:
        cleaned_title = remove_html_tags(original_title)
    json_obj["title"] = cleaned_title

pickle_file_path = "../data/dataset_5k.pickle"

with open(pickle_file_path, 'wb') as pickle_file:
    pickle.dump(db, pickle_file)


