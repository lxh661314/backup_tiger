"""webadmins URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
static_path = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

from devops import views as devops_views
from backupPlatform import views as backup_views
from login import views as login_views
from index import views as index_views


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^index/', index_views.index),
    url(r'^celery_index/', index_views.celery_index),
    url(r'^api/test', backup_views.api_test),
    url(r'^$', login_views.login_home_page),
    url(r'^api/cmdb/cmdb_host_information', devops_views.cmdb_host_information.as_view()),
    url(r'^api/cmdb/cmdb_storage_information', devops_views.cmdb_storage_information.as_view()),

    url(r'^api/backup/backup_host_manager', backup_views.backup_host_manager.as_view()),
    url(r'^api/backup/backup_database_manager', backup_views.backup_database_manager.as_view()),
    url(r'^api/backup/backup_fs_manager', backup_views.backup_fs_manager.as_view()),
    url(r'^api/backup/backup_policy_manager', backup_views.backup_policy_manager.as_view()),
    url(r'^api/backup/backup_history_list', backup_views.backup_history_list.as_view()),
    url(r'^api/backup/backup_policy_sched_manager', backup_views.backup_policy_sched_manager.as_view()),

    url(r'^api/auth/login', login_views.account_login),
    url(r'^api/auth/logout', login_views.account_logout),
    url(r'^api/auth/account_login_info', login_views.account_login_info.as_view()),
    url(r'^api/auth/account_current_user', login_views.account_current_user.as_view()),
]

urlpatterns += static_path

