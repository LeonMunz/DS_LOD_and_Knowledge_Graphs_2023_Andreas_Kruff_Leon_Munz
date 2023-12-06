import pickle
import json
from pyalex import Works, Authors, Sources, Institutions, Concepts, Publishers, Funders
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

def scrape_authors_batch(author_ids):
    results = []
    for author_id in author_ids:
        try:
            works_query = Authors()[author_id]
            results.append(works_query)
        except Exception as e:
            print(f"Error for author {author_id}: {e}")
    return results

def create_author_id_list(json_file):
    author_list = []
    for i in db:
        for j in i["authorships"]:
            if j["author"]["id"] not in author_list:
                author_list.append(j["author"]["id"])
    return author_list

if __name__ == "__main__":

    dbfile = open('../data/dataset_5k.pickle', 'rb')
    db = pickle.load(dbfile)

    author_list = create_author_id_list(db)
    results_list = []

    batch_size = 4  # You can adjust this based on your preference
    milestone_step = 50
    milestone = milestone_step

    with ThreadPoolExecutor() as executor:
        for i in range(0, len(author_list), batch_size):
            batch = author_list[i:i+batch_size]
            futures = executor.submit(scrape_authors_batch, batch)
            results_list.extend(futures.result())
            if len(results_list) >= milestone:
                print(f"Number of scraped authors: {len(results_list)}")
                milestone += milestone_step

    pickle_file_path = "../data/author_data.pkl"
    with open(pickle_file_path, 'wb') as pickle_file:
        pickle.dump(results_list, pickle_file)

