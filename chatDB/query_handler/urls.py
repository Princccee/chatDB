from django.urls import path
from .views import QueryView
from .views import connect_to_mysql

urlpatterns = [
    path('api/query/', QueryView.as_view(), name='query'),
    path('connect-database/', connect_to_mysql, name='connect-database'),
]

