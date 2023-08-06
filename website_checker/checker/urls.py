from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),  # This is the home view for entering website URLs
    path('download_csv/', views.download_csv, name='download_csv'),  # This is the CSV download view
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
