from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.static import serve
from django.views.decorators.http import require_GET
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


@require_GET
def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("api/health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/accounts/",   include("apps.accounts.urls.api")),
    path("api/common/",    include("apps.common.urls.api")),
    path("api/customers/",  include("apps.customers.urls.api")),
    path("api/suppliers/",  include("apps.suppliers.urls.api")),
    path("api/inventory/",  include("apps.inventory.urls.api")),
    path("api/purchasing/", include("apps.purchasing.urls.api")),
    path("api/sales/",      include("apps.sales.urls.api")),
    path("api/routes/",     include("apps.routes.urls.api")),
    path("api/payments/",   include("apps.payments.urls.api")),
    path("api/expenses/",   include("apps.expenses.urls.api")),
    path("api/reporting/",  include("apps.reporting.urls.api")),
    path("api/etims/",      include("apps.etims.urls.api")),
    path("api/preorders/",  include("apps.preorders.urls.api")),
    path("api/printing/",   include("apps.printing.urls.api")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r"^media/products/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT / "products"},
            name="product-image",
        ),
    ]