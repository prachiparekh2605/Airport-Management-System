import os
import sys

# Ensure root project directory is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

class VercelPathMiddleware:
    """
    WSGI Middleware for Vercel Serverless environment:
    Vercel edge rewrites forward requests to /api/index.py.
    This middleware restores the original requested path (e.g. /login, /dashboard, /static/...)
    from Vercel headers so Flask router matches pages and static assets correctly.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO', '')
        if path_info in ('/api/index', '/api/index.py', '/api', ''):
            matched = (
                environ.get('HTTP_X_MATCHED_PATH') or
                environ.get('HTTP_X_VERCEL_PATH') or
                environ.get('REQUEST_URI') or
                environ.get('RAW_URI') or
                environ.get('HTTP_X_FORWARDED_URI')
            )
            if matched:
                path_only = matched.split('?')[0]
                if path_only and path_only not in ('/api/index', '/api/index.py', '/api'):
                    environ['PATH_INFO'] = path_only

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run()
