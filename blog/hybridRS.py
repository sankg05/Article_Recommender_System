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

        self.blog_df.drop_duplicates(['title', 'content'], inplace=True)

        # Preprocess the blog content
        lst_stopwords = corpus.stopwords.words('english')
        self.blog_df['clean_blog_content'] = self.blog_df['content'].apply(
            lambda x: self.pre_process_text(x, flg_stemm=False, flg_lemm=True, lst_stopwords=lst_stopwords)
        )
        self.tfidf_vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.blog_df['clean_blog_content'])
        self.cosine_sim = cosine_similarity(self.tfidf_matrix)

    def pre_process_text(text, flg_stemm=False, flg_lemm=True, lst_stopwords=None):
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
        user_ratings = self.rating_df[self.rating_df['user_id'] == user_id]
        high_rated_blogs = user_ratings[user_ratings['rating'] >= 3.5]['blog_id'].values
        recommended_blogs = []
        for blog_id in high_rated_blogs:
            temp_id = self.blog_df[self.blog_df['blog_id'] == blog_id].index.values[0]
            similar_blogs = self.blog_df[self.cosine_sim[temp_id] > 0.2]['blog_id'].values
            recommended_blogs.extend([b for b in similar_blogs if b not in high_rated_blogs])
        return recommended_blogs

    # Genre/Topic-Based Recommendation
    def get_genre_recommendations(self, user_id, user_preferences):
        merged_df = pd.merge(self.rating_df, self.blog_df[['blog_id', 'topic']], on='blog_id')
        vectorizer = CountVectorizer()
        user_topic_matrix = vectorizer.fit_transform(self.preferences_df)
        new_user_vector = vectorizer.transform([" ".join([t.replace(" ", "_") for t in user_preferences])])
        user_similarity = cosine_similarity(new_user_vector, user_topic_matrix).flatten()
        most_similar_user_id = self.preferences_df.iloc[user_similarity.argmax()]['user_id']
        recommended_blogs = merged_df[merged_df['user_id'] == most_similar_user_id].sort_values(by='rating', ascending=False)[['blog_id', 'category']]
        return recommended_blogs['blog_id'].tolist(), self.preferences_df

    # Collaborative Filtering

    def get_collaborative_recommendations(self, user_id):
        # Create a pivot table with users as rows and blogs as columns
        user_blog_matrix = self.rating_df.pivot(index='user_id', columns='blog_id', values='ratings').fillna(0)

        # Fit the NearestNeighbors model
        model_knn = NearestNeighbors(metric='cosine', algorithm='auto')
        model_knn.fit(user_blog_matrix)

        # Find the k nearest neighbors for the given user
        user_index = user_blog_matrix.index.tolist().index(user_id)
        distances, indices = model_knn.kneighbors([user_blog_matrix.iloc[user_index]], n_neighbors=6)  # Including the user itself

        # Aggregate blog ratings from neighbors (excluding the target user itself)
        similar_users_indices = indices.flatten()[1:]
        similar_users = user_blog_matrix.iloc[similar_users_indices]
        mean_ratings = similar_users.mean(axis=0)

        # Filter out blogs already rated by the target user
        rated_blogs = user_blog_matrix.loc[user_id]
        unrated_blogs = rated_blogs[rated_blogs == 0].index
        recommended_blogs = mean_ratings[unrated_blogs].sort_values(ascending=False).head(5)

        return recommended_blogs.index.tolist()


    def display_user_history(self, user_id):
        user_rated_blogs = self.rating_df[self.rating_df['user_id'] == user_id]
        if user_rated_blogs.empty:
            return f"No rating history found for user {user_id}."
        rated_blogs_details = pd.merge(user_rated_blogs, self.blog_df, on='blog_id')[['title', 'rating', 'category']]
        return rated_blogs_details

    def get_top_categories(user_id, user_preferences, top_topics_df):
        """Get the top categories for the given user or prompt for new categories."""
        if user_id in top_topics_df['user_id'].values:
            # Get top topics for the user
            user_topics = top_topics_df[top_topics_df['user_id'] == user_id]['category'].values[0]
            print(f"Using top topics for user {user_id}: {user_topics}")
            return user_topics
        else:
            # Use the provided preferences
            print(f"User {user_id} not found. Using provided categories: {user_preferences}")
            return user_preferences

    def sort_blogs_by_average_rating(self):
        """Sort blogs by their average ratings."""
        blog_ratings_avg = self.rating_df.groupby('blog_id')['rating'].mean().reset_index()
        blog_ratings_avg.columns = ['blog_id', 'avg_rating']
        sorted_blogs = pd.merge(blog_ratings_avg, self.blog_df, on='blog_id').sort_values(by='avg_rating', ascending=False)
        return sorted_blogs

    # Unified Recommendation Function
    def recommend_blogs(self, user_id, user_preferences):
        """Unified recommendation function with capped recommendations."""
        # Get recommendations and top_topics_df
        genre_recommendations, top_topics_df = self.get_genre_recommendations(user_id, user_preferences)

        # Get categories based on user_id or provided preferences
        user_categories = self.get_top_categories(user_id, user_preferences, top_topics_df)

        # Get recommendations from other methods
        content_recommendations = self.get_content_based_recommendations(user_id)
        collaborative_recommendations = self.get_collaborative_recommendations(user_id)

        # Combine all recommendations
        all_recommendations = set(content_recommendations + genre_recommendations + collaborative_recommendations)

        # Cap the recommendations to 20
        recommended_blogs = self.blog_df[self.blog_df['blog_id'].isin(all_recommendations)][['blog_id', 'title', 'category']]
        if len(recommended_blogs) < 20:
            # Fill the gap with top average-rated blogs from the user's categories
            sorted_blogs = self.sort_blogs_by_average_rating()
            top_category_blogs = sorted_blogs[sorted_blogs['category'].isin(user_categories)]
            remaining_blogs = 20 - len(recommended_blogs)
            additional_blogs = top_category_blogs.head(remaining_blogs)
            recommended_blogs = pd.concat([recommended_blogs, additional_blogs])

        # Ensure the recommendations are capped to 20
        return recommended_blogs.head(20)