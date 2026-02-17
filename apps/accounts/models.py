from django.db import models
from django.contrib.auth.models import AbstractUser
import secrets
from django.utils import timezone
from datetime import timedelta


def generate_email_verification_code():
    for _ in range(10):
        candidate = f"{secrets.randbelow(1_000_000):06d}"
        if not EmailVerificationToken.objects.filter(token=candidate).exists():
            return candidate
    raise ValueError("Unable to generate a unique verification code")


class User(AbstractUser):
    ROLE_CHOICES = (
        ('USER', 'Regular User'),
        ('MODERATOR', 'Moderator'),
        ('CLUB_ADMIN', 'Club Admin'),
        ('SUPER_ADMIN', 'Super Admin'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USER')
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
    def is_email_verified(self):
        return self.email_verified
    
    class Meta:
        ordering = ['-created_at']



#email verification token model
class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.CharField(max_length=6, unique=True, default=generate_email_verification_code)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Verification token for {self.user.email}"
# Create your models here.
