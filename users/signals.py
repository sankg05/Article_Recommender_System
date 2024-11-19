from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile
from django.contrib.auth.signals import user_logged_in
from django.shortcuts import redirect, reverse
from blog.models import UserPreference

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(user_logged_in)
def check_user_preferences(sender, request, user, **kwargs):
    print(f"User {user.username} has logged in.")  # This will print to your console
    user_preferences, created = UserPreference.objects.get_or_create(user=user)

    print(user_preferences.preference.all())  # Use `.all()` to get the queryset of preferences

    # Check if preferences are empty
    if not created and user_preferences.preference.count() == 0:
        print("No preferences set, redirecting to preference form...")
        return redirect(reverse('set_preferences'))