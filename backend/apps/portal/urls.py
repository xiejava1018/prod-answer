# Portal URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'portal/products', views.PortalProductViewSet, basename='portal-product')
router.register(r'portal/solutions', views.SolutionViewSet, basename='portal-solution')
router.register(r'portal/resources', views.ResourceViewSet, basename='portal-resource')

# 统计数据视图
stats_view = views.PortalStatsViewSet.as_view({'get': 'list'})

urlpatterns = [
    # 包含路由器的URL
    path('', include(router.urls)),
    
    # 统计数据
    path('portal/stats/', stats_view, name='portal-stats'),
]
