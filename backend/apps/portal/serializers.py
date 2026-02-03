# Portal API Serializers

from rest_framework import serializers
from apps.products.models import Product
from .models import Solution, Resource, PortalViewLog


class PortalProductSerializer(serializers.ModelSerializer):
    """门户产品列表序列化器"""
    
    feature_count = serializers.SerializerMethodField()
    key_features = serializers.SerializerMethodField()
    subsystem_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'version',
            'vendor',
            'description',
            'subsystem_type',
            'subsystem_type_display',
            'category',
            'is_featured',
            'sort_weight',
            'thumbnail',
            'tagline',
            'key_benefits',
            'view_count',
            'download_count',
            'portal_published_at',
            'created_at',
            'updated_at',
            # 计算字段
            'feature_count',
            'key_features',
        ]
    
    def get_feature_count(self, obj):
        """获取功能数量"""
        return obj.features.filter(is_active=True).count()
    
    def get_key_features(self, obj):
        """获取关键功能（前3个）"""
        features = obj.features.filter(is_active=True)[:3]
        return [f.level3_function or f.level2_function or f.level1_function 
                for f in features if f.level3_function or f.level2_function or f.level1_function]
    
    def get_subsystem_type_display(self, obj):
        """获取子系统类型显示名称"""
        type_map = {
            'asset_mapping': '资产测绘',
            'exposure_mapping': '暴露面管理',
            'big_data': '安全大数据',
            'soar': '自动化编排',
            'comprehensive': '综合安全',
        }
        return type_map.get(obj.subsystem_type, obj.subsystem_type)


class PortalProductDetailSerializer(PortalProductSerializer):
    """门户产品详情序列化器"""
    
    features = serializers.SerializerMethodField()
    spec_metadata_display = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    
    class Meta(PortalProductSerializer.Meta):
        fields = PortalProductSerializer.Meta.fields + [
            'features',
            'spec_metadata',
            'spec_metadata_display',
            'banner_image',
            'seo_title',
            'seo_description',
            'seo_keywords',
            'target_industries',
            'related_products',
        ]
    
    def get_features(self, obj):
        """获取功能树"""
        from collections import defaultdict
        
        features = obj.features.filter(is_active=True).order_by(
            'level1_function', 'level2_function', 'level3_function'
        )
        
        # 构建功能树
        tree = defaultdict(lambda: defaultdict(list))
        
        for feature in features:
            level1 = feature.level1_function or '未分类'
            level2 = feature.level2_function
            level3 = feature.level3_function
            
            if level2:
                if level3:
                    tree[level1][level2].append({
                        'name': level3,
                        'description': feature.description,
                        'indicator_type': feature.indicator_type,
                        'importance_level': feature.importance_level,
                    })
                else:
                    tree[level1][level2].append({
                        'name': level2,
                        'description': feature.description,
                        'indicator_type': feature.indicator_type,
                        'importance_level': feature.importance_level,
                    })
            else:
                # 只有一级功能
                tree[level1][''].append({
                    'name': level1,
                    'description': feature.description,
                    'indicator_type': feature.indicator_type,
                    'importance_level': feature.importance_level,
                })
        
        # 转换为列表格式
        result = []
        for level1, level2_dict in tree.items():
            level1_item = {
                'name': level1,
                'children': []
            }
            
            for level2, features in level2_dict.items():
                if level2:
                    level1_item['children'].append({
                        'name': level2,
                        'children': features
                    })
                else:
                    level1_item['children'].extend(features)
            
            result.append(level1_item)
        
        return result
    
    def get_spec_metadata_display(self, obj):
        """获取规格参数显示格式"""
        if not obj.spec_metadata:
            return {}
        
        # 按类别分组
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for key, value in obj.spec_metadata.items():
            # 简单的分组逻辑（可以根据实际需求调整）
            if any(k in key.lower() for k in ['性能', '速度', '容量', '大小']):
                category = '性能指标'
            elif any(k in key.lower() for k in ['系统', '环境', '平台']):
                category = '系统要求'
            elif any(k in key.lower() for k in ['部署', '安装', '配置']):
                category = '部署信息'
            else:
                category = '其他'
            
            grouped[category].append({
                'name': key,
                'value': value
            })
        
        return dict(grouped)
    
    def get_related_products(self, obj):
        """获取相关产品（同类别或同厂商）"""
        from django.db.models import Q
        
        # 同类别产品
        same_category = Product.objects.filter(
            category=obj.category,
            is_active=True,
            is_on_portal=True
        ).exclude(id=obj.id)[:3]
        
        # 同厂商产品
        same_vendor = Product.objects.filter(
            vendor=obj.vendor,
            is_active=True,
            is_on_portal=True
        ).exclude(id=obj.id)[:3]
        
        # 合并并去重
        related = list(same_category) + list(same_vendor)
        unique_related = list({p.id: p for p in related}.values())[:4]
        
        return PortalProductSerializer(unique_related, many=True).data


class PortalProductCompareSerializer(serializers.ModelSerializer):
    """产品对比序列化器"""
    
    feature_count = serializers.SerializerMethodField()
    feature_tree = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'version',
            'vendor',
            'description',
            'subsystem_type',
            'category',
            'feature_count',
            'feature_tree',
            'spec_metadata',
            'view_count',
            'download_count',
        ]
    
    def get_feature_count(self, obj):
        """获取功能数量"""
        return obj.features.filter(is_active=True).count()
    
    def get_feature_tree(self, obj):
        """获取功能树（简化版）"""
        features = obj.features.filter(is_active=True)
        tree = {}
        
        for feature in features:
            level1 = feature.level1_function or '未分类'
            level2 = feature.level2_function or '未分类'
            level3 = feature.level3_function
            
            if level1 not in tree:
                tree[level1] = {}
            
            if level2 not in tree[level1]:
                tree[level1][level2] = []
            
            if level3:
                tree[level1][level2].append(level3)
        
        return tree


class SolutionSerializer(serializers.ModelSerializer):
    """解决方案序列化器"""
    
    products_count = serializers.SerializerMethodField()
    solution_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Solution
        fields = [
            'id',
            'name',
            'solution_type',
            'solution_type_display',
            'category',
            'summary',
            'pain_points',
            'architecture',
            'architecture_image',
            'benefits',
            'case_study_title',
            'case_study_content',
            'case_study_results',
            'products_count',
            'is_featured',
            'sort_weight',
            'view_count',
            'published_at',
            'created_at',
        ]
    
    def get_products_count(self, obj):
        """获取关联产品数量"""
        return obj.products.filter(is_active=True, is_on_portal=True).count()
    
    def get_solution_type_display(self, obj):
        """获取解决方案类型显示名称"""
        return obj.get_solution_type_display()


class SolutionDetailSerializer(SolutionSerializer):
    """解决方案详情序列化器"""
    
    products = PortalProductSerializer(many=True, read_only=True)
    
    class Meta(SolutionSerializer.Meta):
        fields = SolutionSerializer.Meta.fields + ['products']


class ResourceSerializer(serializers.ModelSerializer):
    """资源序列化器"""
    
    resource_type_display = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Resource
        fields = [
            'id',
            'title',
            'resource_type',
            'resource_type_display',
            'product',
            'product_name',
            'file',
            'file_size',
            'file_size_display',
            'description',
            'excerpt',
            'cover_image',
            'duration',
            'download_count',
            'published_at',
            'created_at',
        ]
    
    def get_resource_type_display(self, obj):
        """获取资源类型显示名称"""
        return obj.get_resource_type_display()
    
    def get_file_size_display(self, obj):
        """获取文件大小显示格式"""
        if not obj.file_size:
            return '0 B'
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"
    
    def get_product_name(self, obj):
        """获取产品名称"""
        if obj.product:
            return obj.product.name
        return None


class PortalViewLogSerializer(serializers.ModelSerializer):
    """访问日志序列化器"""
    
    class Meta:
        model = PortalViewLog
        fields = '__all__'
        read_only_fields = ['created_at']


class PortalStatsSerializer(serializers.Serializer):
    """门户统计数据序列化器"""
    
    total_products = serializers.IntegerField()
    total_features = serializers.IntegerField()
    total_solutions = serializers.IntegerField()
    total_resources = serializers.IntegerField()
    total_views = serializers.IntegerField(required=False)
    total_downloads = serializers.IntegerField(required=False)
    
    subsystem_types = serializers.ListField(required=False)
    categories = serializers.ListField(required=False)
    vendors = serializers.ListField(required=False)