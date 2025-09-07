"""
Custom middleware for logging requests
"""
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('request_logger')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests with client details
    """
    
    def process_request(self, request):
        """Log incoming request details"""
        request.start_time = time.time()
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Get user info if authenticated
        user_info = 'Anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_info = f"User:{request.user.id} ({request.user.username})"
        
        logger.info(
            f"REQUEST: {request.method} {request.path} | "
            f"IP: {client_ip} | "
            f"User: {user_info} | "
            f"User-Agent: {user_agent[:100]}"
        )
        
        return None
    
    def process_response(self, request, response):
        """Log response details"""
        if hasattr(request, 'start_time'):
            duration = round((time.time() - request.start_time) * 1000, 2)  # in milliseconds
            
            # Get user info if authenticated
            user_info = 'Anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info = f"User:{request.user.id} ({request.user.username})"
            
            logger.info(
                f"RESPONSE: {request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration}ms | "
                f"User: {user_info}"
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
