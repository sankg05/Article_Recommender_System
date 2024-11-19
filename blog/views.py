from typing import Optional
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Posts, Interaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.
def home(request):
    posts = Posts.objects.all()
    
    # Calculate average ratings for each post
    for post in posts:
        post.avg_rating = post.average_rating()  # Adding the average rating to each post
    
    context = {
        'posts': posts
    }
    return render(request, 'blog/home.html', context)

class PostListView(ListView):
    model = Posts
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

class UserPostListView(ListView):
    model = Posts
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 3

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