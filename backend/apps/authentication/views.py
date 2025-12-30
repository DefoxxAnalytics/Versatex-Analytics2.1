"""
Authentication views
"""
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from .models import Organization, UserProfile, AuditLog
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    OrganizationSerializer, UserProfileSerializer,
    ChangePasswordSerializer, AuditLogSerializer
)
from .permissions import IsAdmin, IsManager
from .utils import (
    log_action, record_failed_login, check_login_lockout,
    clear_failed_logins, log_security_event
)


def set_jwt_cookies(response, refresh_token):
    """
    Set HTTP-only cookies for JWT tokens.
    This prevents JavaScript access to tokens, mitigating XSS attacks.
    """
    jwt_settings = settings.SIMPLE_JWT

    # Set access token cookie
    response.set_cookie(
        key=jwt_settings.get('AUTH_COOKIE', 'access_token'),
        value=str(refresh_token.access_token),
        max_age=int(jwt_settings['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        secure=jwt_settings.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
        httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
        samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
    )

    # Set refresh token cookie
    response.set_cookie(
        key=jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
        value=str(refresh_token),
        max_age=int(jwt_settings['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        secure=jwt_settings.get('AUTH_COOKIE_SECURE', not settings.DEBUG),
        httponly=jwt_settings.get('AUTH_COOKIE_HTTP_ONLY', True),
        samesite=jwt_settings.get('AUTH_COOKIE_SAMESITE', 'Lax'),
        path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
    )

    return response


def clear_jwt_cookies(response):
    """
    Clear JWT cookies on logout.
    """
    jwt_settings = settings.SIMPLE_JWT

    response.delete_cookie(
        key=jwt_settings.get('AUTH_COOKIE', 'access_token'),
        path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
    )
    response.delete_cookie(
        key=jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token'),
        path=jwt_settings.get('AUTH_COOKIE_PATH', '/'),
    )

    return response


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Log action
        log_action(
            user=user,
            action='create',
            resource='user',
            resource_id=str(user.id),
            details={'username': user.username},
            request=request
        )

        # Create response with user data (no tokens in body for security)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)

        # Set tokens as HTTP-only cookies
        return set_jwt_cookies(response, refresh)


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='dispatch')
class LoginView(generics.GenericAPIView):
    """
    User login endpoint
    Rate limited to 5 attempts per minute per IP to prevent brute force attacks
    Additional lockout after 5 failed attempts for 15 minutes
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']

        # Check for user-specific lockout (after we have username)
        if check_login_lockout(request, username):
            log_security_event('login_blocked_lockout', request)
            return Response(
                {'error': 'Too many failed attempts. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        user = authenticate(
            username=username,
            password=serializer.validated_data['password']
        )

        if not user:
            # Record failed login attempt
            is_locked, remaining = record_failed_login(request, username)
            error_msg = 'Invalid credentials'
            if remaining > 0:
                error_msg += f' ({remaining} attempts remaining)'
            elif is_locked:
                error_msg = 'Too many failed attempts. Please try again later.'

            return Response(
                {'error': error_msg},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            # Don't reveal account exists but is disabled
            record_failed_login(request, username)
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not hasattr(user, 'profile') or not user.profile.is_active:
            # Don't reveal profile status
            record_failed_login(request, username)
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Successful login - clear failed attempts for this user
        clear_failed_logins(request, username)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Log action
        log_action(
            user=user,
            action='login',
            resource='auth',
            details={'username': user.username},
            request=request
        )

        # Create response with user data (no tokens in body for security)
        response = Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })

        # Set tokens as HTTP-only cookies
        return set_jwt_cookies(response, refresh)


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint
    Blacklists the refresh token and clears cookies
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Log action first
        log_action(
            user=request.user,
            action='logout',
            resource='auth',
            request=request
        )

        # Get refresh token from cookie or body (backwards compatibility)
        jwt_settings = settings.SIMPLE_JWT
        refresh_token = request.COOKIES.get(
            jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        ) or request.data.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                # Token is invalid or already blacklisted - still logout successfully
                pass

        # Create response and clear cookies
        response = Response({'message': 'Logout successful'})
        return clear_jwt_cookies(response)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Get and update current user information
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        # Log action
        log_action(
            user=request.user,
            action='update',
            resource='user',
            resource_id=str(request.user.id),
            request=request
        )
        
        return response


class ChangePasswordView(generics.GenericAPIView):
    """
    Change user password
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log action
        log_action(
            user=user,
            action='update',
            resource='password',
            request=request
        )
        
        return Response({'message': 'Password changed successfully'})


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Organization CRUD
    Only admins can create/update/delete organizations
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # Users can only see their own organization
        if self.request.user.is_superuser:
            return Organization.objects.all()
        
        if hasattr(self.request.user, 'profile'):
            return Organization.objects.filter(id=self.request.user.profile.organization.id)
        
        return Organization.objects.none()


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for UserProfile management
    Admins can manage users in their organization
    """
    serializer_class = UserProfileSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # Users can only see profiles in their organization
        if not hasattr(self.request.user, 'profile'):
            return UserProfile.objects.none()
        
        return UserProfile.objects.filter(
            organization=self.request.user.profile.organization
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs
    Only managers and admins can view logs
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        # Users can only see logs from their organization
        if not hasattr(self.request.user, 'profile'):
            return AuditLog.objects.none()

        return AuditLog.objects.filter(
            organization=self.request.user.profile.organization
        )


class CookieTokenRefreshView(generics.GenericAPIView):
    """
    Custom token refresh endpoint that reads refresh token from HTTP-only cookie
    and sets new tokens as HTTP-only cookies.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get refresh token from cookie
        jwt_settings = settings.SIMPLE_JWT
        refresh_token = request.COOKIES.get(
            jwt_settings.get('AUTH_COOKIE_REFRESH', 'refresh_token')
        )

        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Validate and rotate the refresh token
            refresh = RefreshToken(refresh_token)

            # Create response and set new cookies
            response = Response({'message': 'Token refreshed successfully'})
            return set_jwt_cookies(response, refresh)
        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
