from django.db import connection
from ninja_extra import ControllerBase, api_controller, route
from ninja_extra.permissions import AllowAny

from .schemas import HealthOut


@api_controller("/health", tags=["Health"], permissions=[AllowAny])
class HealthController(ControllerBase):
    @route.get("", response=HealthOut, url_name="health-check")
    def health_check(self, request):
        """Check API health and database connectivity."""
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_ok = True
        except Exception:
            pass

        return {
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
        }
