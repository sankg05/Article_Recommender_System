from django.contrib import admin
from .models import Posts, Category, UserPreference, Interaction
# Register your models here.

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category')

admin.site.register(Posts, PostAdmin)
admin.site.register(Category)
admin.site.register(UserPreference)
admin.site.register(Interaction)

