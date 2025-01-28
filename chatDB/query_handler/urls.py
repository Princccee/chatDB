from django.urls import path
from .views import QueryView, get_db_connection

urlpatterns = [
    path('api/query/', QueryView.as_view(), name='query'),
    path('connect-database/', get_db_connection, name='connect-database'),
]
