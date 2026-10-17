class AdminIPRestrictionMiddleware:
def init(self, get_response):
self.get_response = get_response

def __call__(self, request):
    return self.get_response(request)
