import logging
from functools import wraps

logger = logging.getLogger('myapp')


def log_upload_usuario(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        request = None
        if args and hasattr(args[0], 'request'):
            request = args[0].request
        elif args and hasattr(args[0], 'user'):
            request = args[0]
        
        response = view_func(*args, **kwargs)
        
        if request and hasattr(request, 'FILES') and request.FILES:
            user_email = request.user.email if request.user.is_authenticated else 'Anonymous'
            files = list(request.FILES.keys())
            logger.info(f"Upload by {user_email}: {', '.join(files)}")
        
        return response
    
    return wrapper


def log_upload_usuario_method(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        response = func(self, *args, **kwargs)
        
        if self.request.user.is_authenticated and self.request.FILES:
            user_email = self.request.user.email
            num_files = len(self.request.FILES)
            logger.info(f"Upload by {user_email}: {num_files} file(s)")
        
        return response
    
    return wrapper
