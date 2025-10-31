#!/usr/bin/env python
"""Clean database: remove all users except 'fab' and all applications"""

from django.contrib.auth import get_user_model
from apps.applications.models import Application

# Delete all applications
app_count = Application.objects.count()
Application.objects.all().delete()
print(f'✅ Deleted {app_count} applications')

# Delete all users except fab
User = get_user_model()
users_to_delete = User.objects.exclude(username='fab')
user_count = users_to_delete.count()
users_to_delete.delete()
print(f'✅ Deleted {user_count} users')

# Show remaining
remaining_users = User.objects.all()
print(f'✅ Remaining users: {list(remaining_users.values_list("username", flat=True))}')
print(f'✅ Remaining apps: {Application.objects.count()}')
print('✨ Database cleaned successfully!')
