from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Category(models.Model):
    catName = models.CharField(max_length=30)

    def __str__(self):
        return self.catName

class Posts(models.Model):
    title=models.CharField(max_length=100)
    content=models.TextField()
    date_posted=models.DateTimeField(default=timezone.now)
    author=models.ForeignKey(User, on_delete=models.CASCADE)
    category=models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    
    def __str__(self):
        return self.title
