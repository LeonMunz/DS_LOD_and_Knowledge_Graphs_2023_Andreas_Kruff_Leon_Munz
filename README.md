# MiBoAlex
Enhancing OpenAlex by Aggregations and LLMs for the field of Microbiology

### OpenAlex - Concepts:
> - Microbiology
> - Isolation (microbiology)
> - Flora (microbiology)
> - Medical microbiology
> - Clinical microbiology


### Data Structure:
>**Paper**
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


>**Journal**
> 
> - hasID - id
> - isOA

>**Volume**
> relatedJournal  - **name**


> **Authors:** 
> - hasID - **id**
> - hasName - ‘corresponding_author_ids’ => match divergent author names[OA-IDs]
> - hasInstitution - ‘corresponding_institution_ids' => match divergent institution names[OA-IDs]
> - hasFirstAutorship - **Paper**
> - hasAutorship - **Paper**
