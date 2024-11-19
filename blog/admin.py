from django.contrib import admin
from .models import Posts, Category, UserPreference, Interaction
# Register your models here.

admin.site.register(Posts)
admin.site.register(Category)
admin.site.register(UserPreference)
admin.site.register(Interaction)


