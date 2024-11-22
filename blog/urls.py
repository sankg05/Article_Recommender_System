from django.urls import path, register_converter
from . import views
from .views import PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView, UserPostListView, SubmitRatingView, SearchResultsView

class FloatConverter:
    regex = r'\d+(\.\d+)?'  # Matches integers and floats

    def to_python(self, value):
        return float(value)  # Converts the matched string to a Python float

    def to_url(self, value):
        return str(value)  # Converts the Python float back to a string for URL construction

# Register the converter
register_converter(FloatConverter, 'float')

urlpatterns = [
    path('', PostListView.as_view(), name='blog-home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('about/', views.about, name='blog-about'),
    path('rate/<int:post_id>/<float:rating>/', SubmitRatingView.as_view(), name='submit-rating'),
    path("search/", SearchResultsView.as_view(), name="search-results"),
]
