import openpyxl
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from blog.models import Posts, Category
from django.db import transaction
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Import posts from an Excel file into the Posts table with custom post IDs and linked authors.'

    def handle(self, *args, **kwargs):
        # Path to the Excel file
        excel_file = 'blog\management\commands\sampled_blogs.xlsx'

        # Load the workbook and select the active sheet
        wb = openpyxl.load_workbook(excel_file)
        sheet = wb.active

        # Prepare lists to hold objects for bulk_create
        posts_to_create = []

        # Default user in case author_id does not exist
        default_user, created = User.objects.get_or_create(username='SanikaG')

        # Fixed predefined categories (only these categories will be used)
        fixed_categories = set(Category.objects.values_list('catName', flat=True))

        # Iterate through the rows in the Excel sheet (skip header row)
        for row in tqdm(sheet.iter_rows(min_row=2, values_only=True)):
            blog_id = row[0]  # Custom post ID
            author_id = row[1]  # Author's ID
            blog_title = row[2]  # Post title
            blog_content = row[3]  # Post content
            blog_link = row[4]  # Post URL
            topic = row[6]  # Category topic

            # Fetch the user/author based on author_id, if not found, use default user
            try:
                author = User.objects.get(id=author_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User with id {author_id} not found. Using default user 'SanikaG' for post '{blog_title}'."))
                author = default_user

            # Check if the category is one of the fixed categories
            if topic in fixed_categories:
                category = Category.objects.get(catName=topic)
            else:
                # If the category does not exist, log a warning and skip this post
                self.stdout.write(self.style.WARNING(f"Category '{topic}' not found in the fixed categories list. Skipping post '{blog_title}'."))
                continue  # Skip this post and move to the next

            # Create the post object (we are assigning a custom blog_id)
            post = Posts(
                id=blog_id,  # Custom post ID
                title=blog_title,
                content=blog_content,
                post_url=blog_link,
                author=author,
                category=category
            )
            posts_to_create.append(post)

        # Bulk create the posts (if any)
        if posts_to_create:
            with transaction.atomic():  # Ensure atomicity for bulk creation
                Posts.objects.bulk_create(posts_to_create)

        self.stdout.write(self.style.SUCCESS('Successfully imported posts from Excel.'))
