# Project: MiBoAlex
## Mapping Microbiology: Unveiling Trends and Entities through a Research Knowledge Graph

Module: LOD - Linked-Open Data and Knowledge Grahs

Lecturer: Prof. Dr. Konrad Förstner

Participants: Andreas Kruff & Leon Munz

```
Creation of a Neo4J Graph based on bibliographical informations in the research field of Microbiology from OpenAlex in 
order to allow users to interactively explore the research filed to grasp informations about relevant entitys.
```

**Keywords:** Knowledge Graphs, Neo4J, OpenAlex, Microbiology, Named Entity Recognition

## Setup the Environment:

For creating the necessary environment to be able to use this Repository a requirements.txt is provided to install the necessary libararies in your environment

For installing the dependencies use:

```shell 

pip install -r requirements.txt

```

For creating and starting the docker image of Neo4J:

1. Start Docker on your computer
2. ```shell 
   cd docker-neo4j
   ``` 
3. ```shell
   docker-compose up
   ```
4. Enter http://localhost:7888/browser/ in your browser to access Neo4J interface
   
( If Login did not work,  Credentials are Username: neo4j , Password: password )

5. To stop the docker instance terminate the process in the terminal with Strg + c and type 
```shell
docker-compose down
```

## Description:

This repository was created as part of the examination of the module Linked-Open Data and Knowledge Grahs 2023/24 (Master Digital Science) and contains the used code, part of the used datasets and the project presentation and related images from this project.

#### Structure of this Repository
* `data\`: Datasets used creation of the Property Graph in Neo4J
* `project_presentation\`: Powerpoint presentation regarding the project
* `code\`: Code implementation for the Preprocessing, the Data Acquisition and Knowledge Graph Creation
* `jupyters\`: Notebooks for Data Exploration and Data Enrichment
* `docker-neo4j\`: Contains .yml file for creating the Neo4J docker instance within this folder 
* `images\`: Exemplary images from the project regarding different usecases

#### Description of the python files
| Filename                    | Description                                                                                                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `./code/extractReferencesFromDump.py` | Contains the code for extracting additional referenced article metadata from the complete OpenAlex dump |
| `./code/neo4J_import.py` | Contains the code for the preprocessing the underlying data and creating Entity Relations in a Neo4J Graph |
| `./code/scrape_author_info.py` | Contains the code scraping additional author metadata from the OpenAlex API |


## Impressions :

### UML Diagram for the Knowledge Graph Schema
<img src="https://raw.githubusercontent.com/LeonMunz/MiBoAlex/main/images/LOD_UML.svg">

## Potential Usecases:

### Usecase 1: Identify relevant authors in the field of Microbiology in the past

#### Query:

```cypher
MATCH (a:Article)
WHERE a.AmountCites > 5000 AND a.PublicationYear < 2000
WITH a
MATCH (a)<-[:hasFirstAuthor]-(author:author)
MATCH (a)-[hasPublicationYear]->pubyear:pub_year)
RETURN a, author, pubyear;
```

#### Description:

The generated graph illustrates authors who held the position of the first author in papers published before the year 
2000 and garnered more than 5000 citations. Additionally, the inclusion of the "pub_year" entity facilitates the visual 
identification of the most significant authors across the specified years.


#### Resulting Graph

<img src="https://raw.githubusercontent.com/LeonMunz/MiBoAlex/main/images/Usecase_1.svg">

### Usecase 2: Identify Journals and Organizations that are highly participating in the research regarding "Escherichia coli Infections"

#### Query:

```cypher
MATCH (a:Article)-[:hasMeshTopic]->(mesh:Mesh {name: 'Escherichia coli Infections'})
WITH a, mesh
MATCH (a)-[:PublishedIn]->(journal:Journal)
WITH a, mesh, journal
MATCH (journal)-[:refersTo]-(org:Organization)
RETURN a, mesh, journal, org;
```

#### Description:

The generated graph illustrates journals and related organizations that participate in the research of
"Escherichia coli Infections".

#### Resulting Graph

<img src="https://raw.githubusercontent.com/LeonMunz/MiBoAlex/main/images/Usecase_2.svg">

### Usecase 3: Identify Journals and Organizations that have exceptionally high APCs (article processing charge)

#### Query:

```cypher
MATCH (a:Article)
WHERE a.PriceInUSD > 8000
WITH a
MATCH (a)-[:PublishedIn]->(journal:Journal)
WITH a, journal
MATCH (journal)-[:refersTo]-(org:Organization)
WITH a, journal, org
MATCH (a)-[:ActualPricePaid]->(price:Price_in_$)
RETURN a, journal, org, price;
```

#### Description:

The generated graph illustrates journals and related organizations that have exceptionally high APC prices. 
Additionally, the inclusion of the aggregated entity "Price_in_$" facilitates the visual identification of the most 
costly journals for publishing in Open Access in this field.

#### Resulting Graph

<img src="https://raw.githubusercontent.com/LeonMunz/MiBoAlex/main/images/Usecase_3.svg">

### Usecase 4: Identify research topics in microbiology that have exceptionally high APC costs in the corresponding journals 

#### Query:

```cypher
MATCH (a:Article)
WHERE a.PriceInUSD > 11500
WITH a
MATCH (a)-[:PublishedIn]->(journal:Journal)
WITH a, journal
MATCH (journal)-[:refersTo]-(org:Organization)
WITH a, journal, org
MATCH (a)-[:hasMeshTopic]->(mesh:Mesh)
RETURN a, journal, org, mesh;
```

#### Description:

The generated graph illustrates mesh topics that have exceptionally high APC prices. 

#### Resulting Graph

<img src="https://raw.githubusercontent.com/LeonMunz/MiBoAlex/main/images/Usecase_4.svg">


## References:


Used datasets:











### OpenAlex - Concepts:
> - Microbiology
> - Isolation (microbiology)
> - Flora (microbiology)
> - Medical microbiology
> - Clinical microbiology


### Data Structure:
**Paper**
> 
> - hasID - **id**
> - hasDOI -  **doi**
> - hasTitle - **title**
> - hasPublicationDate - **publication_date**
> - hasCanonicalIDs - **ids**
> - hasType - **type**
> - isOA - **open_access**
> - hasOAStatus - **open_access**
> - hasTopic - **keywords**
> - relatedTo - **concepts**
> - hasMeshTopic - **mesh**
> - publishedIn - **locations**
> - hasCited - **referenced_works** (transformed from ID to name)
> - <span style="color:red;">isViable</span> - **is_retracted**
> - <span style="color:red;">hasPosition </span>- biblio - PaperPositionIn - Volume
> - <span style="color:red;">totalRefs </span>- **referenced_works_count**
> - hasCited - **referenced_works (transformed from ID to name)**
> - <span style="color:red;">ActualPricePaid</span> - **apc_paid (just in $)**
> - <span style="color:red;">CountOfCites</span> - cited_by_count
> - <span style="color:red;">hasPosition</span> - biblio
> - <span style="color:red;"> publishedInVol</span> -  Volume 


**Journal**
> - hasID - id
> - isOA

**Volume**
> - relatedJournal  - **name**


**Authors:** 
> - hasID - **id**
> - hasName - ‘corresponding_author_ids’ => match divergent author names[OA-IDs]
> - hasInstitution - ‘corresponding_institution_ids' => match divergent institution names[OA-IDs]
> - hasFirstAutorship - **Paper**
> - hasAutorship - **Paper**
