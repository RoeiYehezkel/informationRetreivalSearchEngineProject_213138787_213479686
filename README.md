# Information Retreival Search Engine Project 213138787_213479686
here is Github repository with the code to the information retreival project.
## Backend.ipynb
the backend of the search engine

### methods:

#### load_pkl_from_bucket
loading the pkl files from bucket
#### get_document_vectors
retrieving document vectors from an inverted index with TF-IDF values.
Args:
inverted_index: A dictionary where keys are unique terms and values are postings lists.
Each postings list is a list of tuples (document_id, tfidf_value).

Returns:
A dictionary where keys are document IDs and values are lists representing
sparse document vectors (containing only non-zero TF-IDF values).

#### create_sparse_vector_from_counter
creating a sparse vector from a query represented as a counter.

Args:
  query_counter: A Counter object representing the query, where keys are tokens and values are counts.
  vocab: A list of unique terms.

Returns:
  A sparse vector representing the query, with non-zero counts at indices corresponding to tokens in the vocab.

### working stages:
1) loading pkl files from bucket
2) tokenize & stemming of query
3) create sparse vactor from query counter
4) extract the posting lists, convert them to vectors
5) calculating cosine similarity
