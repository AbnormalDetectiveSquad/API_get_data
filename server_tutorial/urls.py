"""
URL configuration for server_tutorial project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from collector.views import (
    home_view,
    collect_data_citywall_view,
    collect_data_road_view,
    collect_data_living_view,
    collect_data_section_view,
    collect_data_direction_view,
    collect_data_DivRoad_view,
)

urlpatterns = [
    path('', home_view, name='home'),

    # 아래 5개 URL을 통해 서로 다른 API를 호출
    path('collect_citywall/',    collect_data_citywall_view,    name='collect_citywall'),
    path('collect_road/',        collect_data_road_view,        name='collect_road'),
    path('collect_living/',      collect_data_living_view,      name='collect_living'),
    path('collect_section/',     collect_data_section_view,     name='collect_section'),
    path('collect_direction/',   collect_data_direction_view,   name='collect_direction'),
    path('collect_divroad/',   collect_data_DivRoad_view,   name='collect_divroad'),
]
