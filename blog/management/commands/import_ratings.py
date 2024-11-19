import openpyxl
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Posts, Interaction
from django.db import transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Import interactions from an Excel file into the Interaction table.'

    def handle(self, *args, **kwargs):
        # Path to the Excel file
        excel_file = 'blog/management/commands/sampled_ratings.xlsx'

        # Load the workbook and select the active sheet
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        # Prepare a list to hold objects for bulk_create
        interactions_to_create = []

        # Iterate through the rows in the Excel sheet (skip header row)
        for row in tqdm(sheet.iter_rows(min_row=2, values_only=True)):
            blog_id = row[0]  # Blog ID
            user_id = row[1]  # User ID
            rating = row[2]  # Rating

            # Validate foreign keys
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User with id {user_id} not found. Skipping interaction for blog_id {blog_id}."))
                continue  # Skip this interaction

            try:
                blog = Posts.objects.get(id=blog_id)
            except Posts.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Blog with id {blog_id} not found. Skipping interaction for user_id {user_id}."))
                continue  # Skip this interaction

            # Create the Interaction object using correct field names
            interaction = Interaction(
                user_id=user,  # Correct field name in the model
                blog_id=blog,  # Correct field name in the model
                rating=rating
            )
            interactions_to_create.append(interaction)

        # Bulk create the interactions (if any)
        if interactions_to_create:
            with transaction.atomic():  # Ensure atomicity for bulk creation
                Interaction.objects.bulk_create(interactions_to_create)

        self.stdout.write(self.style.SUCCESS('Successfully imported interactions from Excel.'))
