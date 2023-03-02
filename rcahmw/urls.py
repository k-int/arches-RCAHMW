from django.conf.urls import include, url
from django.conf import settings
from django.conf.urls.static import static
from .views.ciimchanges import ChangesView, ConceptsExportView

urlpatterns = [
    url(r'^', include('arches.urls')),
    url(r"^resource/changes", ChangesView.as_view(), name="ChangesView"),
    url(r"^concept/export", ConceptsExportView.as_view(), name="ConceptsExportView"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
