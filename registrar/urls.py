"""registrar URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

import logging
import os

from auth_backends.urls import oauth2_urlpatterns
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic.base import RedirectView
from edx_api_doc_tools import make_api_info, make_docs_ui_view

from . import api_renderer
from .apps.api import urls as api_urls
from .apps.core import views as core_views


logger = logging.getLogger(__name__)


admin.site.site_header = 'Registrar Service Administration'
admin.site.site_title = admin.site.site_header
admin.autodiscover()

app_name = 'registrar'
api_description_path = os.path.join(settings.PROJECT_ROOT, 'static', 'api-description.html')
with open(api_description_path, encoding='utf-8') as api_description_file:
    new_api_ui_view = make_docs_ui_view(
        make_api_info(
            title="Registrar API - Online Documentation",
            version="v2",
            email="masters-dev@edx.org",
            description=api_description_file.read(),
        )
    )

urlpatterns = oauth2_urlpatterns + [
    # '/' and '/login' redirect to '/login/',
    # which attempts LMS OAuth and then redirects to api-docs.
    url(r'^/?$', RedirectView.as_view(url=settings.LOGIN_URL)),
    url(r'^login$', RedirectView.as_view(url=settings.LOGIN_URL)),

    # Use the same auth views for all logins,
    # including those originating from the browseable API.
    url(r'^api-auth/', include(oauth2_urlpatterns)),

    # NEW Swagger documentation UI, generated using edx-api-doc-tools.
    # TODO: Make this the default as part of MST-195.
    url(r'^api-docs/new$', RedirectView.as_view(pattern_name='api-docs-new')),
    url(r'^api-docs/new/$', new_api_ui_view, name='api-docs-new'),

    # Swagger documentation UI.
    # TODO: Remove as part of MST-195.
    url(r'^api-docs$', RedirectView.as_view(pattern_name='api-docs')),
    url(r'^api-docs/$', api_renderer.render_yaml_spec, name='api-docs'),

    # Django admin panel.
    url(r'^admin$', RedirectView.as_view(pattern_name='admin:index')),
    url(r'^admin/', admin.site.urls),

    # Health view.
    url(r'^health/?$', core_views.health, name='health'),

    # Auto-auth for testing. View raises 404 if not `settings.ENABLE_AUTO_AUTH`
    url(r'^auto_auth/?$', core_views.AutoAuth.as_view(), name='auto_auth'),

    # The API itself!
    url(r'^api/', include(api_urls)),
]

# edx-drf-extensions csrf app
urlpatterns += [
    url(r'', include('csrf.urls')),
]

if settings.DEBUG and os.environ.get('ENABLE_DJANGO_TOOLBAR', False):  # pragma: no cover
    try:
        import debug_toolbar
    except ImportError:
        logger.exception(
            "ENABLE_DJANGO_TOOLBAR is true, but debug_toolbar could not be imported."
        )
    else:
        urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
