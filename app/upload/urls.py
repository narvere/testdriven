from django.urls import path
from . import views

urlpatterns = [
    path("x/", views.start_page, name="start"),
    path('qqq/''', views.start_page, name='start'),

]

# if bool(settings.DEBUG):
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
