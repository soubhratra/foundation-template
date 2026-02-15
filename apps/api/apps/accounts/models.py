from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model. Extend with additional fields as needed.

    IMPORTANT: This model MUST exist before the first migration.
    Changing AUTH_USER_MODEL after migrations have run requires
    database recreation.
    """

    class Meta:
        db_table = "users"
