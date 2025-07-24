from django.urls import path
from .views import MarkCheckerView, HistoryListView, HistoryDetailView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', MarkCheckerView.as_view(), name='mark_checker'),
    path('history/', HistoryListView.as_view(), name='history_list'),
    path('history/<int:pk>/', HistoryDetailView.as_view(), name='history_detail'),
]