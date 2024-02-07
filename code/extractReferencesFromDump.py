import pandas as pd
import pickle
import time
import os

def create_file_path_list():
    """
    Generating list of files in the works directory of the complete OpenAlex dump

    Parameters
    -----------

    Returns
    -----------
    filepath_list : list
        List containing all the paths within the works directory

    """

    # Define the path to the works directory of the OpenAlex dump
    root = "../data/openalex-snapshot/data/works"

    filepath_list = []

    # Using the os library to walk through the directory and append all paths to the list
    for path, subdirs, files in os.walk(root):
        for name in files:
            filepath_list.append(os.path.join(path, name))


    return filepath_list

def create_workslist():
    """
    Extract the relevant referenced works IDs from the 5000 test samples

    Parameters
    ----------

    Returns
    ----------
    df_referenced_articles : DataFrame
          DataFrame containing the IDs from the referenced articles
    """

    # Loading the 5000 test sample
    dbfile = open('../data/dataset_5k.pickle', 'rb')
    db = pickle.load(dbfile)

    # Extracting the referenced works from the file
    liste_ref_ids = []
    for i in db:
        for j in i["referenced_works"]:
            liste_ref_ids.append(j)

    # Delete ID duplicates
    works_list = list(set(liste_ref_ids))

    # Save referenced works list as DataFrame
    df_referenced_articles = pd.DataFrame({"id": works_list})

    return df_referenced_articles

def read_gz_iteratively(path, chunksize, df_referenced_articles):
    """
    Decompress and read gzipped files to extract additional metadata for the referenced articles

    Parameters
    ----------
    path : String
        String containing the path to a file of the works directory

    chunksize: int
        Amount of rows that are loaded in a dataframe at once

    df_referenced_articles: DataFrame
        DataFrame containing the IDs from the referenced articles

    Returns
    ----------
    full_result_df : DataFrame
        Contains the metadata of the IDs that were found in the dump so far
    df_referenced_articles : DataFrame
        Updated version exluding the already found IDs


    """

    full_result_df = pd.DataFrame()

    reader = pd.read_json(path, compression='gzip', lines=True, encoding='utf-8', chunksize=chunksize)

    for chunk_df in reader:
        chunk_df = chunk_df[['id', 'title']]
        result = pd.merge(chunk_df, df_workslist, on="id", how="inner")
        full_result_df = pd.concat([full_result_df, result], ignore_index=True)
        df_workslist = df_workslist[~df_workslist["id"].isin(result["id"])]

    return full_result_df, df_workslist


if __name__ ==  "__main__":
    # Generate a list of all paths from the works directory
    works_df = create_workslist()

    # Initialize Dataframe for saving the metadata of the IDs
    RefArt_metadata_df = pd.DataFrame()

    # Generate a list of all referenced article IDs that need to be enriched with metadata
    file_list = create_file_path_list()
    counter = 0

    # Iterate through the gzipped files and extract the metadata for the referenced articles and concatinate them
    # to the RefArt_metadata_df

    for i in file_list:
        counter += 1
        works_df_len = len(works_df)
        df, works_df = read_gz_iteratively(i, chunksize=50000, df_workslist=works_df)

        RefArt_metadata_df = pd.concat([RefArt_metadata_df, df], ignore_index=True)

        # Saves and instance of the found metadata every 100 files in case that an error occurs
        if counter % 100 == 0:
            RefArt_metadata_df.to_csv(f'existing_df_{counter}.csv', index=False)
            RefArt_metadata_df = pd.DataFrame()  # Create a new DataFrame

