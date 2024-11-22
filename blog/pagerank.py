import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import networkx as nx

class PageRank(object):
    def __init__(self, user_preference, blogData):
        self.user_preference = user_preference
        self.blogData = blogData

        self.vectorizer = TfidfVectorizer(stop_words = 'english')
        self.tf_idf_matrix = self.vectorizer.fit_transform(self.blogData['blog_content'])
            