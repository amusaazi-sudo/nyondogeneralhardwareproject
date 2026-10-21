import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

ROLES = ["admin", "stock_manager", "sales_manager"]


class Command(BaseCommand):
    help = "Create the role groups and a demo login for visitors."

    def handle(self, *args, **options):
        # Create the three role groups if they don't exist yet
        for name in ROLES:
            Group.objects.get_or_create(name=name)

        # The demo password comes from an environment variable, not the code
        password = os.environ.get("DEMO_PASSWORD")
        if not password:
            self.stdout.write("DEMO_PASSWORD is not set, so no demo user was created.")
            return

        user, created = User.objects.get_or_create(username="demo")
        user.set_password(password)
        user.is_superuser = False  # no access to the Django admin site
        user.is_staff = False
        user.save()
        user.groups.set([Group.objects.get(name="admin")])

        self.stdout.write(self.style.SUCCESS("Demo user is ready."))