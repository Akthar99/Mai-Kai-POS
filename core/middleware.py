"""
Custom Security Middleware
"""
import logging
import re
from django.core.cache import cache
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.security')


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware to prevent brute force attacks
    """
    def process_request(self, request):
        if request.path.startswith('/staff/login/'):
            ip = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip}'
            attempts = cache.get(cache_key, 0)
            
            if attempts >= 5:
                logger.warning(f'Rate limit exceeded for IP: {ip}')
                return HttpResponseForbidden(
                    '<h1>Too Many Requests</h1>'
                    '<p>Too many login attempts. Please try again in 5 minutes.</p>'
                )
            
        return None
    
    def process_response(self, request, response):
        if request.path.startswith('/staff/login/') and request.method == 'POST':
            if response.status_code in [200, 302]:
                # Check if login failed
                if hasattr(response, 'context') and response.context:
                    if response.context.get('error'):
                        ip = self.get_client_ip(request)
                        cache_key = f'login_attempts_{ip}'
                        attempts = cache.get(cache_key, 0)
                        cache.set(cache_key, attempts + 1, 300)  # 5 minutes
                        logger.warning(f'Failed login attempt from IP: {ip}')
                else:
                    # Successful login - clear attempts
                    ip = self.get_client_ip(request)
                    cache_key = f'login_attempts_{ip}'
                    cache.delete(cache_key)
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add additional security headers
    """
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.tailwindcss.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self';"
            )
        
        return response


class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """
    Basic SQL injection detection and blocking
    """
    # Common SQL injection patterns
    SQL_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(--)",
        r"(;.*\b(select|insert|update|delete|drop)\b)",
        r"(\bexec\b.*\()",
        r"(\bor\b.*=.*)",
        r"('.*or.*'.*=.*')",
    ]
    
    def process_request(self, request):
        # Skip admin panel and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        # Check GET parameters
        for key, value in request.GET.items():
            if self._contains_sql_injection(str(value)):
                logger.error(f'SQL injection attempt in GET parameter: {key}={value} from IP: {self._get_ip(request)}')
                return HttpResponseBadRequest('Invalid request parameters')
        
        # Check POST parameters
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self._contains_sql_injection(str(value)):
                    logger.error(f'SQL injection attempt in POST parameter: {key} from IP: {self._get_ip(request)}')
                    return HttpResponseBadRequest('Invalid request data')
        
        return None
    
    def _contains_sql_injection(self, value):
        """Check if value contains SQL injection patterns"""
        value_lower = value.lower()
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    def _get_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

