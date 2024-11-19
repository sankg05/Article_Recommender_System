import openpyxl
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile
from django.db import transaction
from django.db.utils import IntegrityError
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Import users from an Excel file into the User table with custom IDs and optional empty fields.'

    def handle(self, *args, **kwargs):
        # Path to the Excel file
        excel_file = 'users/management/commands/sampled_authors.xlsx'

        # Load the workbook and select the first sheet
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        # List to hold new User objects to create
        users_to_create = []
        users_to_update = []

        # Iterate through the rows in the Excel sheet (skip the header row)
        for row in tqdm(sheet.iter_rows(min_row=2, values_only=True)):
            password = 'password123#'
            
            # Access the values by index instead of string keys
            author_id = row[0]        # Assuming 'author_id' is in the first column
            author_name = row[1]      # Assuming 'author_name' is in the second column

            # Try to get or update the user based on the custom id
            user, created = User.objects.update_or_create(
                id=author_id,  # Set the custom user ID
                defaults={
                    'username': author_name,
                    'password': password,
                    'email': f"user_{author_id}@example.com"  # Optional email
                }
            )

            if created:
                # Only hash the password if the user is being created (new user)
                user.set_password(password)
                users_to_create.append(user)
            else:
                # Update password if the user already exists
                user.set_password(password)  # Make sure to hash the password even on updates
                users_to_update.append(user)

        # Now handle users_to_create using bulk_create
        if users_to_create:
            User.objects.bulk_create(users_to_create)

        # Save users that need to be updated
        for user in users_to_update:
            user.save()  # Update existing users with the new details

        # Create profiles for each user (even for existing ones, if needed)
        for user in users_to_create + users_to_update:
            Profile.objects.get_or_create(user=user)

        # Optional: Reset the sequence so Django handles new IDs automatically
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT setval('auth_user_id_seq', (SELECT MAX(id) FROM auth_user))")

        self.stdout.write(self.style.SUCCESS('Successfully imported users from Excel.'))
