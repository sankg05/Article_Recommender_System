from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MaxValueValidator
from django.db.models import Avg

class Category(models.Model):
    catName = models.CharField(max_length=30)

    def __str__(self):
        return self.catName

class Posts(models.Model):
    title=models.CharField(max_length=100)
    content=models.TextField()
    date_posted=models.DateTimeField(default=timezone.now)
    post_url = models.URLField(null = False)
    author=models.ForeignKey(User, on_delete=models.CASCADE)
    category=models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    
    def __str__(self):
        return self.title
    
    def average_rating(self) -> float:
        return Interaction.objects.filter(blog_id=self).aggregate(Avg("rating"))["rating__avg"] or 0
    
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk':self.pk})
    
class UserPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    preference = models.ManyToManyField(Category, blank = True)

    def __str__(self):
        return f"{self.user.username}'s Preferences"

class Interaction(models.Model):
    user_id = models.ForeignKey(User, on_delete = models.CASCADE)
    blog_id = models.ForeignKey(Posts, on_delete = models.CASCADE)
    rating = models.DecimalField(default = 0.0, max_digits=2, decimal_places=1, validators=[MaxValueValidator(5.0)])