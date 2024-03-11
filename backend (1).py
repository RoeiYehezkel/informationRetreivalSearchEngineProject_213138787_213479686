# -*- coding: utf-8 -*-
"""Backend.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ii0HLZSu_PpvuQvZ4AGCFGB6BSCrQwwO
"""

import pickle
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/content/gcp-413611-9c6c29adaf10.json"


import sys
import pyspark
from collections import Counter, OrderedDict, defaultdict
import itertools
from itertools import islice, count, groupby
import pandas as pd
import os
import re
from operator import itemgetter
import nltk
from nltk.stem.porter import *
from nltk.corpus import stopwords
from time import time
from pathlib import Path
import pickle
import pandas as pd
from google.cloud import storage
from scipy.sparse import dok_matrix
from pyspark.ml.linalg import Vectors

import math
import hashlib
def _hash(s):
    return hashlib.blake2b(bytes(s, encoding='utf8'), digest_size=5).hexdigest()

nltk.download('stopwords')

from google.cloud import storage
import pickle

def load_pkl_from_bucket(bucket_name, file_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download the blob as bytes
    serialized_data = blob.download_as_bytes()

    # Deserialize the bytes into Python object
    loaded_data = pickle.loads(serialized_data)

    return loaded_data

bucket_name = 'proj_479_187'
path_pst = 'pst.pkl'
path_doc_to_title = 'doc_to_title.pkl'
path_w2dfdict = 'w2dfdict.pkl'
path_vocab_dct_title = 'vocab_dct_title.pkl'

pst = load_pkl_from_bucket(bucket_name, path_pst)
doc_to_title = load_pkl_from_bucket(bucket_name, path_doc_to_title)
w2dfdict = load_pkl_from_bucket(bucket_name, path_w2dfdict)
vocab_dct_title = load_pkl_from_bucket(bucket_name, path_vocab_dct_title)

def get_document_vectors(postings, vocab):
    """
    This function retrieves document vectors from an inverted index with TF-IDF values.

    Args:
      inverted_index: A dictionary where keys are unique terms and values are postings lists.
          Each postings list is a list of tuples (document_id, tfidf_value).

    Returns:
      A dictionary where keys are document IDs and values are lists representing
          sparse document vectors (containing only non-zero TF-IDF values).
    """
    document_vectors = {}
    for term, postings_list in postings:
        for document_id, tfidf_value in postings_list:
          # Leverage document_id as the index for the sparse vector
            sparse_vec_indices = [vocab[term]]
            sparse_vec_values = [tfidf_value]
            # Update or initialize sparse vector for the document
            if document_id in document_vectors:
                  document_vectors[document_id].extend(zip(sparse_vec_indices, sparse_vec_values))
            else:
                  document_vectors[document_id] = list(zip(sparse_vec_indices, sparse_vec_values))
    # Convert the lists of indices and values to sparse vectors
    for doc, lst in document_vectors.items():
        document_vectors[doc] = sorted(lst, key= lambda x: x[0])
    doc_vectors = {doc_id: Vectors.sparse(len(vocab), [x[0] for x in lst], [x[1] for x in lst]) for doc_id, lst in document_vectors.items()}
    return doc_vectors

english_stopwords = frozenset(stopwords.words('english'))
corpus_stopwords = ["category", "references", "also", "external", "links",
                    "may", "first", "see", "history", "people", "one", "two",
                    "part", "thumb", "including", "second", "following",
                    "many", "however", "would", "became"]

all_stopwords = english_stopwords.union(corpus_stopwords)

import numpy as np
import time
def search_backend(query):
    ''' Returns up to a 100 of your best search results for the query. This is
        the place to put forward your best search engine, and you are free to
        implement the retrieval whoever you'd like within the bound of the
        project requirements (efficiency, quality, etc.). That means it is up to
        you to decide on whether to use stemming, remove stopwords, use
        PageRank, query expansion, etc.

        To issue a query navigate to a URL like:
         http://YOUR_SERVER_DOMAIN/search?query=hello+world
        where YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of up to 100 search results, ordered from best to worst where each
        element is a tuple (wiki_id, title).
    '''

    def create_sparse_vector_from_counter(query_counter, vocab):

        """

        This function creates a sparse vector from a query represented as a counter.

        Args:
          query_counter: A Counter object representing the query, where keys are tokens and values are counts.
          vocab: A list of unique terms.

        Returns:
          A sparse vector representing the query, with non-zero counts at indices corresponding to tokens in the vocab.
        """
        # Initialize empty lists for indices and values
        sparse_vec_indices = []
        sparse_vec_values = []
        val_idx = {}
        # Iterate over tokens in the query counter
        for token, count in query_counter.items():
          # Get the index of the token in the vocab list
          if token in vocab:
            term_index = vocab[token]
            # Append the index and count to the sparse vector
#             sparse_vec_indices.append(term_index)
#             sparse_vec_values.append(count)
            val_idx[term_index]=count
        # Create a sparse vector from the indices and values
        val_idx = dict(sorted(val_idx.items(), key=lambda x: x[0]))
        sparse_vector = Vectors.sparse(len(vocab), list(val_idx.keys()), list(val_idx.values()))

        return sparse_vector


    np.seterr(divide='ignore', invalid='ignore')
    stemmer=PorterStemmer()
    RE_WORD = re.compile(r"""[\#\@\w](['\-]?\w){2,24}""", re.UNICODE)
    tokens = [token.group() for token in RE_WORD.finditer(query.lower()) if token.group() not in all_stopwords]
    tokens = [stemmer.stem(token) if len(token) > 1 else token for token in tokens]
    tokens = [token for token in tokens if token in vocab_dct_title.keys()]
    doc_ids = [doc_id for token in tokens for doc_id, _ in w2dfdict[token] if token in w2dfdict]
    count = Counter([token for token in tokens])
    q_vec_title = create_sparse_vector_from_counter(count,vocab_dct_title)
    # Calculate the cosine similarity between the query vector and the document vectors


    stemmer=PorterStemmer()
    RE_WORD = re.compile(r"""[\#\@\w](['\-]?\w){2,24}""", re.UNICODE)
    tokens = [stemmer.stem(token.group()) if len(token.group()) > 1 else token.group() for token in RE_WORD.finditer(query.lower())]
    filtered_vocab = {k: v for k,v in vocab_dct_title.items() if k in tokens}
    pst_filtered = [(term, postings_list) for term, postings_list in pst if term in filtered_vocab]
    document_vectors = get_document_vectors(pst_filtered, vocab_dct_title)
    # Calculate the cosine similarity between the query vector and the document vectors
    def cosine_similarity(vec, column_vector):
        """
        Calculate the cosine similarity between two vectors.
        """
        dot_product = vec.dot(column_vector)
        norm_vec = vec.norm(2)
        norm_column_vector = column_vector.norm(2)
        similarity = dot_product / (norm_vec * norm_column_vector)
        return similarity

    res = []
    for doc_id, vec in document_vectors.items():
        sim_title = cosine_similarity(q_vec_title, vec)
        res.append((doc_id, sim_title))
    docs=[x[0] for x in sorted(res, key=lambda x: x[1], reverse=True)[:30]]
    res = [doc_to_title[key] for key in docs if key in doc_to_title]
    return res