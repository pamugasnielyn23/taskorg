from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class PasswordResetCode(models.Model):
    """Model to store 6-digit verification codes for password reset (Facebook-style)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset code for {self.user.username}"

    def is_valid(self):
        """Check if the code is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def generate_code(cls, user):
        """Generate a new 6-digit code for the user"""
        # Delete any existing unused codes for this user
        cls.objects.filter(user=user, is_used=False).delete()
        
        # Generate a random 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration to 15 minutes from now
        expires_at = timezone.now() + timezone.timedelta(minutes=15)
        
        return cls.objects.create(user=user, code=code, expires_at=expires_at)
