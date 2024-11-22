import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import UserPreference, Category
from django.db import transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Load user preferences from a CSV file into the UserPreference table.'

    def handle(self, *args, **kwargs):
        # Path to the CSV file
        csv_file = 'blog\management\commands\Topics-by-user.csv'

        # Prepare a list for bulk actions
        preferences_to_create = []

        # Open and read the CSV file
        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)

            # Iterate through each row in the CSV file
            for row in tqdm(reader):
                user_id = row['userId']
                top_topics = eval(row['top_topics'])  # Convert string representation of list to actual list

                # Validate user existence
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"User with id {user_id} not found. Skipping."))
                    continue

                # Get or create categories based on `top_topics`
                categories = []
                for topic in top_topics:
                    category, created = Category.objects.get_or_create(catName=topic)
                    categories.append(category)

                # Update or create UserPreference
                try:
                    with transaction.atomic():  # Ensure atomicity for each user
                        user_preference, created = UserPreference.objects.get_or_create(user=user)
                        user_preference.preference.set(categories)  # Set the ManyToMany relation
                        user_preference.save()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing preferences for user_id {user_id}: {e}"))
                    continue

        self.stdout.write(self.style.SUCCESS('Successfully imported user preferences from CSV.'))
