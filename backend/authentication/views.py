import logging
import random
import secrets
from typing import Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from users.models import User, UserProfile

logger = logging.getLogger(__name__)

MAGIC_LINK_TTL = getattr(settings, "MAGIC_LINK_EXPIRY_SECONDS", 600)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _generate_tokens(user: User) -> Tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _build_user_payload(user: User) -> dict:
    profile = getattr(user, "profile", None)
    return {
        "id": user.id,
        "name": user.get_full_name() or user.email,
        "email": user.email,
        "role": user.role,
        "track": user.track,
        "status": user.status,
        "profile": {
            "firstName": profile.first_name if profile else "",
            "lastName": profile.last_name if profile else "",
            "areasOfInterest": profile.areas_of_interest if profile else [],
            "schoolName": profile.school_name if profile else "",
            "yearLevel": profile.year_level if profile else None,
            "country": profile.country if profile else "",
            "region": profile.region if profile else "",
            "availability": profile.availability if profile else "",
            "bio": profile.bio if profile else "",
        },
    }


def _issue_tokens_for_email(email: str) -> Response:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": email},
    )
    if created:
        UserProfile.objects.get_or_create(user=user)
        logger.info("Created new user via magic link: %s", email)

    access_token, refresh_token = _generate_tokens(user)
    return Response(
        {
            "token": access_token,
            "refresh_token": refresh_token,
            "user": _build_user_payload(user),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def request_magic_link(request):
    email = request.data.get("email", "")
    email = _normalize_email(email)

    if not email:
        return Response(
            {"error": "Email is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_email(email)
    except ValidationError:
        return Response(
            {"error": "Invalid email address."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    magic_token = secrets.token_urlsafe(32)
    otp_code = "".join(str(random.randint(0, 9)) for _ in range(6))

    cache.set(f"magic_token:{magic_token}", email, timeout=MAGIC_LINK_TTL)
    cache.set(f"otp:{email}", otp_code, timeout=MAGIC_LINK_TTL)

    magic_link_base = getattr(
        settings,
        "FRONTEND_BASE_URL",
        "https://yourdomain.com",
    )
    magic_link = f"{magic_link_base.rstrip('/')}/auth/verify?token={magic_token}"

    subject = "Login to BIOTech Futures Hub"
    message = (
        f"Use the link or code below to access the BIOTech Futures Hub.\n\n"
        f"Magic Link: {magic_link}\n"
        f"One-Time Code: {otp_code}\n\n"
        f"This link and code will expire in {MAGIC_LINK_TTL // 60} minutes."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
    logger.info("Magic link requested for %s", email)

    return Response(
        {
            "success": True,
            "message": "Magic link sent to your email.",
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    email = _normalize_email(request.data.get("email", ""))
    code = str(request.data.get("code", "")).strip()

    if not email or not code:
        return Response(
            {"error": "Email and code are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cached_code = cache.get(f"otp:{email}")
    if cached_code != code:
        return Response(
            {"error": "Invalid or expired code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cache.delete(f"otp:{email}")
    return _issue_tokens_for_email(email)


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_magic_link(request):
    token = request.query_params.get("token", "")
    if not token:
        return Response(
            {"error": "Token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cache_key = f"magic_token:{token}"
    email = cache.get(cache_key)
    if not email:
        return Response(
            {"error": "Invalid or expired magic link."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cache.delete(cache_key)
    cache.delete(f"otp:{email}")
    return _issue_tokens_for_email(email)


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    refresh_token_value = request.data.get("refresh_token", "")
    if not refresh_token_value:
        return Response(
            {"error": "Refresh token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        refresh = RefreshToken(refresh_token_value)
        access_token = str(refresh.access_token)
    except TokenError:
        return Response(
            {"error": "Invalid or expired refresh token."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return Response(
        {
            "token": access_token,
            "refresh_token": str(refresh),
        }
    )
