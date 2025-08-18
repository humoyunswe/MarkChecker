from django.urls import path
from .views import MarkCheckerView, HistoryListView, HistoryDetailView, MarkLimitView, AggregateLimitView, UpdateArchiveView, DeleteMarkView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', MarkCheckerView.as_view(), name='mark_checker'),
    path('mark-limit/', MarkLimitView.as_view(), name='mark_limit'),
    path('update-archive/', UpdateArchiveView.as_view(), name='update_archive'),
    path('delete-mark/', DeleteMarkView.as_view(), name='delete_mark'),
    path('aggregate-limit/', AggregateLimitView.as_view(), name='aggregate_limit'),
    path('history/', HistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', HistoryDetailView.as_view(), name='history_detail'),
]