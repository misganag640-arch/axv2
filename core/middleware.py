from django.http import HttpResponseForbidden


class AdminIPRestrictionMiddleware:

    ALLOWED_ADMIN_IPS = [
        "127.0.0.1",
        "::1",
        "192.168.43.117",
        "196.189.24.48",
         "192.168.1.2"
        # Add your own public admin IP here when you want to access it on production
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/control-panel/"):
            # Check for proxy header first, fallback to REMOTE_ADDR
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.META.get("REMOTE_ADDR")

            print("ADMIN REQUEST IP:", client_ip)

            # IP restriction check has been removed. 
            # Anyone with valid credentials can now access the admin page.

        return self.get_response(request)
