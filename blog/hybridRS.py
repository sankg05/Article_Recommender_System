import sys
import pandas as pd
import numpy as np
import nltk
import re
from nltk import corpus
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk import wsd
from nltk.corpus import wordnet as wn
from sklearn.feature_extraction.text import CountVectorizer
from collections import defaultdict
from sklearn.neighbors import NearestNeighbors

nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('punkt')
nltk.download('stopwords')

class HybridRecommender(object):

    def __init__(self, blog_df, rating_df, preferences_df):
        self.blog_df = blog_df
        self.rating_df = rating_df
        self.preferences_df = preferences_df

        # Remove duplicates
        self.blog_df.drop_duplicates(['title', 'content'], inplace=True)

        # Preprocess the blog content
        lst_stopwords = corpus.stopwords.words('english')
        self.blog_df['clean_blog_content'] = self.blog_df['content'].apply(
            lambda x: self.pre_process_text(x, flg_stemm=False, flg_lemm=True, lst_stopwords=lst_stopwords)
        )
        self.tfidf_vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.blog_df['clean_blog_content'])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix)

    @staticmethod
    def validate_preferences(user_preferences):
        if not isinstance(user_preferences, list):
            raise ValueError("Invalid user preferences format. Must be a list of strings or dictionaries containing 'preference'.")
        if not all(isinstance(p, str) for p in user_preferences):
            raise ValueError("Invalid user preferences format. Each preference must be a string.")

    @staticmethod
    def pre_process_text(text, flg_stemm=False, flg_lemm=True, lst_stopwords=None):
        """Preprocess text by cleaning, removing stopwords, and applying stemming/lemmatization."""
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        lst_text = text.split()
        if lst_stopwords is not None:
            lst_text = [word for word in lst_text if word not in lst_stopwords]
        if flg_lemm:
            lemmatizer = WordNetLemmatizer()
            lst_text = [lemmatizer.lemmatize(word) for word in lst_text]
        if flg_stemm:
            stemmer = PorterStemmer()
            lst_text = [stemmer.stem(word) for word in lst_text]
        return " ".join(lst_text)

    def get_content_based_recommendations(self, user_id):
        """Get recommendations based on blog content similarity."""
        user_ratings = self.rating_df[self.rating_df['user_id'] == user_id]
        high_rated_blogs = user_ratings[user_ratings['rating'] >= 3.5]['blog_id'].values
        recommended_blogs = []
        for blog_id in high_rated_blogs:
            temp_id = self.blog_df[self.blog_df['blog_id'] == blog_id].index.values[0]
            similar_blogs = self.blog_df[self.cosine_sim[temp_id] > 0.2]['blog_id'].values
            recommended_blogs.extend([b for b in similar_blogs if b not in high_rated_blogs])
        return recommended_blogs

    # def get_genre_recommendations(self, user_id, user_preferences):
    #     """Get recommendations based on genre/topic preferences."""
    #     # Process `user_preferences` to extract strings if needed
    #     if isinstance(user_preferences, list) and all(isinstance(p, dict) for p in user_preferences):
    #         user_preferences = [pref['preference'] for pref in user_preferences]

    #     if not isinstance(user_preferences, list) or not all(isinstance(pref, str) for pref in user_preferences):
    #         raise ValueError("Invalid user preferences format. Must be a list of strings or dictionaries containing 'preference'.")

    #     # Replace spaces in preferences with underscores
    #     processed_preferences = [" ".join([t.replace(" ", "_") for t in user_preferences])]

    #     # Generate similarity matrix
    #     vectorizer = CountVectorizer()
    #     user_topic_matrix = vectorizer.fit_transform(self.preferences_df['preference'])
    #     new_user_vector = vectorizer.transform(processed_preferences)
    #     user_similarity = cosine_similarity(new_user_vector, user_topic_matrix).flatten()

    #     most_similar_user_id = self.preferences_df.iloc[user_similarity.argmax()]['user_id']
    #     merged_df = pd.merge(self.rating_df, self.blog_df[['blog_id', 'category__catName']], on='blog_id')
    #     recommended_blogs = merged_df[merged_df['user_id'] == most_similar_user_id].sort_values(by='rating', ascending=False)[['blog_id', 'category__catName']]
    #     return recommended_blogs['blog_id'].tolist(), self.preferences_df

    def get_collaborative_recommendations(self, user_id):
        """Get recommendations using collaborative filtering."""
        # Create a pivot table
        user_blog_matrix = self.rating_df.pivot(index='user_id', columns='blog_id', values='rating').fillna(0)

        # Fit the NearestNeighbors model
        model_knn = NearestNeighbors(metric='cosine', algorithm='auto')
        model_knn.fit(user_blog_matrix)

        # Find the k nearest neighbors
        user_index = user_blog_matrix.index.tolist().index(user_id)
        distances, indices = model_knn.kneighbors([user_blog_matrix.iloc[user_index]], n_neighbors=6)

        # Aggregate ratings from neighbors
        similar_users_indices = indices.flatten()[1:]
        similar_users = user_blog_matrix.iloc[similar_users_indices]
        mean_ratings = similar_users.mean(axis=0)

        # Filter out blogs already rated by the user
        rated_blogs = user_blog_matrix.loc[user_id]
        unrated_blogs = rated_blogs[rated_blogs == 0].index
        recommended_blogs = mean_ratings[unrated_blogs].sort_values(ascending=False).head(5)

        return recommended_blogs.index.tolist()

    def recommend_blogs(self, user_id, user_preferences):
        """Unified recommendation function."""
        # genre_recommendations, top_topics_df = self.get_genre_recommendations(user_id, user_preferences)
        content_recommendations = self.get_content_based_recommendations(user_id)
        collaborative_recommendations = self.get_collaborative_recommendations(user_id)

        # Combine all recommendations
        all_recommendations = set(content_recommendations + collaborative_recommendations)# genre_recommendations 

        # Cap recommendations to 20
        recommended_blogs = self.blog_df[self.blog_df['blog_id'].isin(all_recommendations)][['blog_id', 'title', 'category__catName']]
        if len(recommended_blogs) < 20:
            sorted_blogs = self.sort_blogs_by_average_rating()
            remaining_blogs = 20 - len(recommended_blogs)
            additional_blogs = sorted_blogs.head(remaining_blogs)
            recommended_blogs = pd.concat([recommended_blogs, additional_blogs])

        return recommended_blogs.head(20)

    def sort_blogs_by_average_rating(self):
        """Sort blogs by average ratings."""
        blog_ratings_avg = self.rating_df.groupby('blog_id')['rating'].mean().reset_index()
        blog_ratings_avg.columns = ['blog_id', 'avg_rating']
        sorted_blogs = pd.merge(blog_ratings_avg, self.blog_df, on='blog_id').sort_values(by='avg_rating', ascending=False)
        return sorted_blogs
