from django.urls import path
from .views import QueryView, connect_database_view
from .utils.nlp_utils import process_query, load_schema

urlpatterns = [
    path('api/query/', QueryView.as_view(), name='query'),
    path('connect-database/', connect_database_view, name='connect-database'),
    # path('process_query/', process_query, name='process_query'),
]
