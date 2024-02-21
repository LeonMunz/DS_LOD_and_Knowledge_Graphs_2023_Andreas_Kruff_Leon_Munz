from Bio import Entrez
import ast
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def get_pubmed_count(query, year):
    Entrez.email = ""  # Insert your Email address here
    search_query = f"{query} AND {year}[DP]"

    handle = Entrez.egquery(term=search_query)
    record = Entrez.read(handle)
    for row in record["eGQueryResult"]:
        if row["DbName"] == "pubmed":
            return int(row["Count"])


if __name__ == "__main__":

    counts = []
    years = []
    query = "microbiology"
    year_range = range(1888, 2025, 1)

    for i in year_range:
        count = get_pubmed_count(query, i)
        counts.append(count)
        years.append(i)
       
    data = {"Year": years, "Count": counts}
   
    df = pd.DataFrame(data)

    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.lineplot(x="Year", y="Count", data=df[:-3], marker='o')

    plt.xlabel("Year of publication")
    plt.ylabel("Amount of Publications in microbiology")

    plt.title("Amount of publications from Pubmed related to the term 'microbiology'")
    plt.show()