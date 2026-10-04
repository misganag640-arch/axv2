from django.http import HttpResponseForbidden


class AdminIPRestrictionMiddleware:

    ALLOWED_ADMIN_IPS = [
        "127.0.0.1",
        "::1",
        "192.168.43.117",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.path.startswith("/control-panel/"):

            client_ip = request.META.get("REMOTE_ADDR")

            print("ADMIN REQUEST IP:", client_ip)

            if client_ip not in self.ALLOWED_ADMIN_IPS:
                return HttpResponseForbidden(
                    f"Access denied. Your IP is: {client_ip}"
                )

        return self.get_response(request)