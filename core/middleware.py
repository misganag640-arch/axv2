class AdminIPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
File "/app/core/middleware.py", line 2
def init(self, get_response):
IndentationError: expected an indented block after class definition
