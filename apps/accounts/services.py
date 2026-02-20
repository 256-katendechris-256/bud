
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import EmailVerificationToken

class EmailVerificationService:
    
    @staticmethod
    def send_verification_email(user, request=None):
        """Send email verification code to user"""
        
        # Delete old tokens
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Create new token
        token = EmailVerificationToken.objects.create(user=user)
        
        verification_url = f"{settings.FRONTEND_URL}/?token={token.token}"
        
        # Email content
        subject = "Verify your Bud account email"
        message = f"""
        Hi {user.first_name},
        
        Welcome to Bud! Use this 6-digit verification code:

        {token.token}

        Or click the link below:
        
        {verification_url}
        
        This code expires in 24 hours.
        
        Thanks,
        Bud Team
        """
        
        # Send email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return token

    @staticmethod
    def verify_email(token_string):
        """Verify email using token"""
        try:
            normalized_token = str(token_string).strip()
            if not normalized_token.isdigit() or len(normalized_token) != 6:
                return False, "Verification code must be a 6-digit number", None

            token = EmailVerificationToken.objects.get(token=normalized_token)
            
            if not token.is_valid():
                return False, "Token expired or already used", None
            
            # Mark email as verified
            token.user.email_verified = True
            token.user.email_verified_at = timezone.now()
            token.user.is_active = True
            token.user.save()
            
            # Mark token as used
            token.is_used = True
            token.save()
            
            return True, "Email verified successfully", token.user
        
        except EmailVerificationToken.DoesNotExist:
            return False, "Invalid token", None
