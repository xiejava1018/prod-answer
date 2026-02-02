# Portal API Views

import uuid
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from apps.products.models import Product
from .models import Solution, Resource, PortalViewLog
from .serializers import (
    PortalProductSerializer,
    PortalProductDetailSerializer,
    PortalProductCompareSerializer,
    SolutionSerializer,
    SolutionDetailSerializer,
    ResourceSerializer,
    PortalStatsSerializer,
)


class PortalProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    门户产品API（只读）
    
    提供产品列表、详情、推荐、对比等功能
    """
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True, is_on_portal=True)
    serializer_class = PortalProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # 筛选字段
    filterset_fields = {
        'subsystem_type': ['exact', 'in'],
        'category': ['exact', 'in'],
        'vendor': ['exact', 'in'],
        'is_featured': ['exact'],
    }
    
    # 搜索字段
    search_fields = [
        'name',
        'description',
        'tagline',
        'vendor',
        'features__level1_function',
        'features__level2_function',
        'features__level3_function',
    ]
    
    # 排序字段
    ordering_fields = [
        'created_at',
        'name',
        'sort_weight',
        'view_count',
        'portal_published_at',
    ]
    ordering = ['-sort_weight', '-portal_published_at']
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'retrieve':
            return PortalProductDetailSerializer
        elif self.action == 'compare':
            return PortalProductCompareSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 预取关联数据，优化查询性能
        if self.action == 'list':
            queryset = queryset.prefetch_related('features')
        elif self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'features',
                'solutions',
                'resources'
            )
        
        return queryset
    
    @method_decorator(cache_page(60 * 5))  # 缓存5分钟
    @method_decorator(vary_on_headers('Authorization', 'Cookie'))
    def list(self, request, *args, **kwargs):
        """获取产品列表"""
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 30))  # 缓存30分钟
    @method_decorator(vary_on_headers('Authorization', 'Cookie'))
    def retrieve(self, request, *args, **kwargs):
        """获取产品详情"""
        instance = self.get_object()
        
        # 增加浏览次数
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # 记录访问日志
        self._log_view(instance)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        获取推荐产品
        
        GET /api/v1/portal/products/featured/
        """
        featured_products = self.get_queryset().filter(
            is_featured=True
        )[:8]
        
        serializer = self.get_serializer(featured_products, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        产品对比
        
        POST /api/v1/portal/products/compare/
        Body: { product_ids: [uuid1, uuid2, uuid3] }
        """
        product_ids = request.data.get('product_ids', [])
        
        # 验证参数
        if not product_ids:
            return Response(
                {'error': '请选择要对比的产品'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(product_ids) < 2:
            return Response(
                {'error': '至少需要选择2个产品进行对比'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(product_ids) > 4:
            return Response(
                {'error': '最多只能选择4个产品进行对比'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 验证UUID格式
        valid_ids = []
        for pid in product_ids:
            try:
                valid_ids.append(uuid.UUID(pid))
            except ValueError:
                return Response(
                    {'error': f'无效的产品ID: {pid}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # 获取产品
        products = self.get_queryset().filter(id__in=valid_ids)
        
        if products.count() < 2:
            return Response(
                {'error': '有效产品数量不足2个'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(products, many=True)
        return Response({
            'count': products.count(),
            'products': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        获取产品统计信息
        
        GET /api/v1/portal/products/statistics/
        """
        queryset = self.get_queryset()
        
        # 基础统计
        stats = {
            'total_products': queryset.count(),
            'total_features': sum(
                p.features.filter(is_active=True).count() 
                for p in queryset
            ),
        }
        
        # 子系统类型分布
        subsystem_stats = queryset.values('subsystem_type').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['subsystem_types'] = list(subsystem_stats)
        
        # 分类分布
        category_stats = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['categories'] = list(category_stats)
        
        # 厂商分布（前10）
        vendor_stats = queryset.values('vendor').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        stats['vendors'] = list(vendor_stats)
        
        return Response(stats)
    
    def _log_view(self, instance):
        """记录访问日志"""
        try:
            # 获取IP地址
            x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = self.request.META.get('REMOTE_ADDR', '')
            
            # 获取User-Agent
            user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # 获取Referer
            referer = self.request.META.get('HTTP_REFERER', '')[:500]
            
            # 创建日志记录
            PortalViewLog.objects.create(
                content_type='product',
                object_id=instance.id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
            )
        except Exception as e:
            # 记录日志失败不影响主流程
            print(f"Failed to log view: {e}")


class SolutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    解决方案API（只读）
    """
    permission_classes = [AllowAny]
    queryset = Solution.objects.filter(is_active=True)
    serializer_class = SolutionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'solution_type': ['exact', 'in'],
        'category': ['exact', 'in'],
        'is_featured': ['exact'],
    }
    
    search_fields = ['name', 'summary', 'pain_points']
    
    ordering_fields = ['sort_weight', 'published_at', 'created_at']
    ordering = ['-sort_weight', '-published_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SolutionDetailSerializer
        return super().get_serializer_class()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                'products',
                'products__features'
            )
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """获取详情并增加浏览次数"""
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """获取推荐解决方案"""
        featured = self.get_queryset().filter(
            is_featured=True
        )[:6]
        
        serializer = self.get_serializer(featured, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


class ResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    资源中心API（只读）
    """
    permission_classes = [AllowAny]
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = ResourceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'resource_type': ['exact', 'in'],
        'product': ['exact'],
    }
    
    search_fields = ['title', 'description', 'excerpt']
    
    ordering_fields = ['published_at', 'created_at', 'download_count']
    ordering = ['-published_at']
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """
        记录下载
        
        POST /api/v1/portal/resources/{id}/download/
        """
        resource = self.get_object()
        
        # 增加下载次数
        resource.download_count += 1
        resource.save(update_fields=['download_count'])
        
        # 返回文件URL（实际下载通过Nginx X-Accel-Redirect）
        file_url = request.build_absolute_uri(resource.file.url)
        file_name = resource.file.name.split('/')[-1]
        
        return Response({
            'download_url': file_url,
            'file_name': file_name,
            'file_size': resource.file_size,
            'message': '下载链接已生成'
        })


class PortalStatsViewSet(viewsets.ViewSet):
    """
    门户统计数据API
    """
    permission_classes = [AllowAny]
    
    def list(self, request):
        """
        获取门户统计数据
        
        GET /api/v1/portal/stats/
        """
        from django.db.models import Sum
        
        # 产品统计
        total_products = Product.objects.filter(
            is_active=True, 
            is_on_portal=True
        ).count()
        
        # 功能特性统计
        total_features = Product.objects.filter(
            is_active=True,
            is_on_portal=True
        ).aggregate(
            total=Sum('features__count')
        )['total'] or 0
        
        # 解决方案统计
        total_solutions = Solution.objects.filter(
            is_active=True
        ).count()
        
        # 资源统计
        total_resources = Resource.objects.filter(
            is_active=True
        ).count()
        
        # 浏览量统计
        total_views = PortalViewLog.objects.count()
        
        # 下载量统计
        total_downloads = Resource.objects.aggregate(
            total=Sum('download_count')
        )['total'] or 0
        
        stats = {
            'total_products': total_products,
            'total_features': total_features,
            'total_solutions': total_solutions,
            'total_resources': total_resources,
            'total_views': total_views,
            'total_downloads': total_downloads,
        }
        
        serializer = PortalStatsSerializer(stats)
        return Response(serializer.data)