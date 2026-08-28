class SimpleLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        print(f"Przetwarzam zapytanie do ścieżki: {request.path}")
        response = self.get_response(request)
        print(f"Zwracam odpowiedź z kodem statusu: {response.status_code}")
        return response