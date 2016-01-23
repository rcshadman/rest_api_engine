from django.conf.urls import url
from . import views
from api.views import Table,Data

urlpatterns = [
    # url(r'table', views.table, name='table'),
    url(r'table', Table.as_view(), name='table'),
    url(r'data', Data.as_view(), name='data'),
    ]