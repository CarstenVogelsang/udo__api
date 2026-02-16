# portal/pim/api/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProduktViewSet
from pim.api_views import SortimentListeView

router = DefaultRouter()
router.register(r'produkte', ProduktViewSet)

urlpatterns = [
    path("sortimente/", SortimentListeView.as_view(), name="api-sortimente"),
]

urlpatterns += router.urls