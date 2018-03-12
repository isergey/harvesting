from django.urls import path
from . import views

app_name = "harvester"

urlpatterns = [
    path('', views.index, name='index'),
    path('sources/', views.sources, name='sources'),
    path('sources/add/', views.add_source, name='add_source'),
    path('sources/<int:id>/', views.source, name='source'),
    path('sources/<int:id>/change', views.change_source, name='change_source'),
    path('sources/<int:id>/delete', views.delete_source, name='delete_source'),
    path('sources/<int:source_id>/records', views.records, name='records'),
    path('sources/<int:source_id>/collect_source', views.collect_source, name='collect_source'),
    path('sources/<int:source_id>/harvesting_status', views.harvesting_status, name='harvesting_status'),
    path('sources/<int:source_id>/files/add', views.add_source_file, name='add_source_file'),
    path('sources/<int:source_id>/files/<int:id>', views.source_file, name='source_file'),
    path('sources/<int:source_id>/files/<int:id>/change', views.change_source_file, name='change_source_file'),
    path('sources/<int:source_id>/files/<int:id>/delete', views.delete_source_file, name='delete_source_file'),
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

    path('indexing_rules/', views.indexing_rules, name='indexing_rules'),
    path('indexing_rules/add', views.add_indexing_rules, name='add_indexing_rules'),
    path('indexing_rules/<int:id>/change', views.change_indexing_rules, name='change_indexing_rules'),
    path('indexing_rules/<int:id>/invoke', views.invoke_indexing_rule, name='invoke_indexing_rule'),
]
