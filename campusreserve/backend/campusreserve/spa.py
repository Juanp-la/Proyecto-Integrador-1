"""
Serves the compiled React frontend (backend/frontend_build/) from Django, so
the whole app works from a single server: http://<server-ip>/ shows the app
and http://<server-ip>/api/... is the API.

To update the frontend after changing it:  cd frontend && npm run build
"""

import mimetypes

from django.conf import settings
from django.http import FileResponse, HttpResponse

# Some servers don't know these types; browsers refuse JS modules without them.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")


def frontend(request, path=""):
    root = settings.FRONTEND_BUILD_DIR.resolve()
    if path:
        candidate = (root / path).resolve()
        # Real file (JS, CSS, images...) -> send it. The parents check blocks "../" tricks.
        if candidate.is_file() and root in candidate.parents:
            response = FileResponse(open(candidate, "rb"))
            if path.startswith("assets/"):
                response["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

    index = root / "index.html"
    if not index.exists():
        return HttpResponse(
            "El frontend no está compilado. Corre: cd frontend && npm run build",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    # Any other route (/, /reservas, ...) -> the React app.
    return FileResponse(open(index, "rb"), content_type="text/html; charset=utf-8")
