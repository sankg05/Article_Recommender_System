from typing import Optional
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, F, Avg
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Posts, Interaction, UserPreference
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .hybridRS import HybridRecommender
from .pagerank import PageRank
import logging
logger = logging.getLogger('django')
import pandas as pd
import os

import sys

# Create your views here.
def home(request):
    posts = Posts.objects.all()
    for post in posts:
        post.avg_rating = post.average_rating()
    
    context = {
        'posts': posts
    }
    return render(request, 'blog/home.html', context)

class SearchResultsView(ListView):
    model = Posts
    template_name = 'blog/search_results.html'

    def get_queryset(self): # new
        query = self.request.GET.get("q")
        return  Posts.objects.filter(
            Q(title__icontains=query) |
            Q(author__username__icontains=query) |
            Q(category__catName__icontains=query)
            )

class PostListView(ListView):
    model = Posts
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    # ordering = ['-date_posted']
    paginate_by = 5

    def get_query(self):
        user = self.request.user
        if user.is_authenticated:
            blog_df, rating_df, preferences_df, preferences_list = get_hybrid_recommendations()
            hyrbidObject = HybridRecommender(blog_df, rating_df, preferences_df)
            final_recommendations = hyrbidObject.recommend_blogs(user.id, preferences_list)
            l = final_recommendations['blog_id']
            print(l)

            return Posts.objects.filter(id__in = l)
        else:
            return Posts.objects.all().order_by('-date_posted')

class UserPostListView(ListView):
    model = Posts
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Posts.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['average_rating'] = self.object.average_rating()
        context['stars'] = range(1, 6)  # 1 to 5 stars
        if self.request.user.is_authenticated:
            interaction = Interaction.objects.filter(user_id=self.request.user, blog_id=self.object).first()
            context['user_rating'] = interaction.rating if interaction else 0  # Ensure this is correct
        return context
            
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Posts
    fields = ['title', 'category', 'content', 'post_url']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Posts
    success_url = '/'
    fields = ['title', 'category', 'content', 'post_url']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
    
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Posts
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False
        
def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})

class SubmitRatingView(View):
    def get(self, request, post_id, rating):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'You must be logged in to rate.'}, status=403)

        post = get_object_or_404(Posts, id=post_id)

        # Get or create the interaction (rating) for the post by the current user
        interaction, created = Interaction.objects.get_or_create(user_id=request.user, blog_id=post)

        # Update the user's rating
        interaction.rating = rating
        interaction.save()

        # Calculate the average rating
        all_ratings = Interaction.objects.filter(blog_id=post)
        total_ratings = all_ratings.count()

        if total_ratings > 0:
            avg_rating = sum([interaction.rating for interaction in all_ratings]) / total_ratings
        else:
            avg_rating = 0  # Default to 0 if there are no ratings yet
        # Send the updated average rating and the user's rating
        return JsonResponse({
            'success': True,
            'message': 'Rating submitted successfully',
            'average_rating': avg_rating,
            'user_rating': rating  # Return the user's rating
        })
    

def get_hybrid_recommendations(request):
    blogData = Posts.objects.all()
    ratingData = Interaction.objects.all()
    preferenceData = UserPreference.objects.all()
    user_preference = UserPreference.objects.filter(user = request.user.id)
    preferences_list = list(user_preference.values())
    print(preferenceData)

    blog_df = pd.DataFrame(list(blogData))
    rating_df = pd.DataFrame(list(ratingData))
    preferences_df = pd.DataFrame(list(preferenceData))

    return blog_df, rating_df, preferences_df, preferences_list

def pagerank_recommendations(request):
    print("Testing if function is called")
    blogData = Posts.objects.all()
    preferences = UserPreference.objects.filter(user = request.user.id)
    preferences_list = list(preferences.values())
    print(preferences_list)

    return blogData, preferences_list
