"""
Custom middleware for security and API versioning.
"""


class DeprecationMiddleware:
    """
    Middleware to add deprecation headers to legacy API endpoints.

    Legacy endpoints (without /v1/ in the path) are deprecated in favor of
    versioned endpoints (/api/v1/...). This middleware adds standard HTTP
    deprecation headers to help clients migrate.

    Headers added:
    - Deprecation: true
    - Sunset: Date when the legacy endpoints will be removed
    - Link: URL to the new versioned endpoint
    """

    # Legacy endpoint prefixes (without /v1/)
    LEGACY_PREFIXES = (
        '/api/auth/',
        '/api/procurement/',
        '/api/analytics/',
    )

    # Sunset date for legacy endpoints (ISO 8601 format)
    SUNSET_DATE = 'Sat, 01 Jun 2025 00:00:00 GMT'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is a legacy endpoint
        path = request.path
        if self._is_legacy_endpoint(path):
            response['Deprecation'] = 'true'
            response['Sunset'] = self.SUNSET_DATE

            # Add link to versioned endpoint
            versioned_path = self._get_versioned_path(path)
            if versioned_path:
                # Use the Link header format from RFC 8594
                response['Link'] = f'<{versioned_path}>; rel="successor-version"'

        return response

    def _is_legacy_endpoint(self, path: str) -> bool:
        """Check if the path is a legacy (non-versioned) endpoint."""
        # Must start with one of the legacy prefixes
        if not any(path.startswith(prefix) for prefix in self.LEGACY_PREFIXES):
            return False

        # Must NOT contain /v1/ (which would make it a versioned endpoint)
        return '/v1/' not in path

    def _get_versioned_path(self, path: str) -> str:
        """Convert a legacy path to its versioned equivalent."""
        # Replace /api/auth/ with /api/v1/auth/, etc.
        for prefix in self.LEGACY_PREFIXES:
            if path.startswith(prefix):
                suffix = path[len(prefix):]
                versioned_prefix = prefix.replace('/api/', '/api/v1/')
                return f'{versioned_prefix}{suffix}'
        return None
