from django.db import models


class CampushubLogin(models.Model):
    """Maps to the existing campushub_login table in PostgreSQL."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=150, unique=True)
    password_hash = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campushub_login'
        managed = False  # Table already exists in pgAdmin

    def __str__(self):
        return self.username
