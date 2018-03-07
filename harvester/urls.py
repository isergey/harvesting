from django.urls import path
from . import views

app_name = "harvester"

urlpatterns = [
    path('', views.index, name='index'),
    path('sources/', views.sources, name='sources'),
    path('sources/<int:id>/', views.source, name='source'),
    path('sources/<int:source_id>/files/<int:id>', views.source_file, name='source_file'),
    path(
        'sources/<int:source_id>/files/<int:id>/calculate_records_count',
        views.calculate_records_count,
        name='calculate_records_count'
    ),
    path(
        'sources/<int:source_id>/files/<int:id>/testing',
        views.source_file_testing,
        name='source_file_testing'
    ),
]
