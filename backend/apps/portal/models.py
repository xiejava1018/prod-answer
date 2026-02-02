# Portal Models

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product


class Solution(models.Model):
    """解决方案模型"""
    
    SOLUTION_TYPE_CHOICES = [
        ('industry', '按行业'),
        ('scenario', '按场景'),
        ('use_case', '按用例'),
    ]
    
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=200, db_index=True)
    solution_type = models.CharField(
        max_length=20,
        choices=SOLUTION_TYPE_CHOICES,
        default='industry'
    )
    category = models.CharField(max_length=100, db_index=True)
    
    # 关联产品（多对多）
    products = models.ManyToManyField(
        Product,
        related_name='solutions',
        blank=True
    )
    
    # 内容
    summary = models.TextField(help_text='解决方案概述')
    pain_points = models.JSONField(
        default=list,
        help_text='核心痛点（JSON数组）'
    )
    architecture = models.TextField(
        blank=True,
        help_text='架构描述'
    )
    architecture_image = models.ImageField(
        upload_to='solution_architectures/%Y/%m/',
        blank=True
    )
    benefits = models.JSONField(
        default=list,
        help_text='实施收益（JSON数组）'
    )
    
    # 案例
    case_study_title = models.CharField(max_length=200, blank=True)
    case_study_content = models.TextField(blank=True)
    case_study_results = models.JSONField(
        default=dict,
        help_text='实施效果数据（JSON）'
    )
    
    # SEO
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    
    # 状态
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_weight = models.IntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # 统计
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'portal_solutions'
        verbose_name = '解决方案'
        verbose_name_plural = '解决方案'
        ordering = ['-sort_weight', '-published_at']
        indexes = [
            models.Index(
                fields=['solution_type', 'category', 'is_active'],
                name='idx_solution_filter'
            ),
            models.Index(
                fields=['is_featured', 'is_active', '-published_at'],
                name='idx_featured_solutions'
            ),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_solution_type_display()})"


class Resource(models.Model):
    """资源中心模型"""
    
    RESOURCE_TYPE_CHOICES = [
        ('document', '产品文档'),
        ('whitepaper', '白皮书'),
        ('case_study', '案例研究'),
        ('video', '视频教程'),
        ('datasheet', '数据手册'),
    ]
    
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=200, db_index=True)
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES
    )
    
    # 关联产品（可选）
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='resources',
        null=True,
        blank=True
    )
    
    # 文件
    file = models.FileField(
        upload_to='resources/%Y/%m/',
        max_length=500
    )
    file_size = models.PositiveIntegerField(
        default=0,
        help_text='文件大小（字节）'
    )
    
    # 描述
    description = models.TextField(blank=True)
    excerpt = models.CharField(
        max_length=300,
        blank=True,
        help_text='摘要（用于列表展示）'
    )
    
    # 封面图（视频或文档）
    cover_image = models.ImageField(
        upload_to='resource_covers/%Y/%m/',
        blank=True
    )
    duration = models.CharField(
        max_length=20,
        blank=True,
        help_text='视频时长（如：12:34）'
    )
    
    # SEO
    seo_title = models.CharField(max_length=200, blank=True)
    seo_description = models.TextField(blank=True)
    
    # 统计
    download_count = models.PositiveIntegerField(default=0)
    
    # 状态
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'portal_resources'
        verbose_name = '资源'
        verbose_name_plural = '资源'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(
                fields=['resource_type', 'is_active', '-published_at'],
                name='idx_resource_filter'
            ),
            models.Index(
                fields=['product', 'resource_type', 'is_active'],
                name='idx_product_resources'
            ),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_resource_type_display()})"


class PortalViewLog(models.Model):
    """门户访问日志"""
    
    CONTENT_TYPE_CHOICES = [
        ('product', '产品'),
        ('solution', '解决方案'),
        ('resource', '资源'),
    ]
    
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    object_id = models.UUIDField()
    
    # 访问信息
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referer = models.URLField(max_length=500, blank=True)
    
    # 地理位置（可选）
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'portal_view_logs'
        verbose_name = '访问日志'
        verbose_name_plural = '访问日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['content_type', 'object_id', '-created_at'],
                name='idx_view_log_content'
            ),
            models.Index(
                fields=['ip_address', '-created_at'],
                name='idx_view_log_ip'
            ),
            models.Index(
                fields=['created_at'],
                name='idx_view_log_date'
            ),
        ]


# 扩展Product模型
from django.db.models import Q

# 动态扩展Product模型
if hasattr(Product, 'is_featured'):
    # 已经扩展过了
    pass
else:
    # 添加门户相关字段
    from django.db import models as db_models
    
    # 门户展示相关
    Product.add_to_class('is_featured', db_models.BooleanField(
        default=False, 
        help_text='是否推荐产品（门户首页展示）'
    ))
    Product.add_to_class('is_on_portal', db_models.BooleanField(
        default=True,
        help_text='是否在门户展示'
    ))
    Product.add_to_class('sort_weight', db_models.IntegerField(
        default=0, 
        help_text='排序权重（值越大越靠前）'
    ))
    Product.add_to_class('thumbnail', db_models.ImageField(
        upload_to='product_thumbnails/%Y/%m/',
        blank=True,
        help_text='产品缩略图（建议尺寸：400x300）'
    ))
    Product.add_to_class('banner_image', db_models.ImageField(
        upload_to='product_banners/%Y/%m/',
        blank=True,
        help_text='产品横幅图（建议尺寸：1200x400）'
    ))
    
    # SEO相关
    Product.add_to_class('seo_title', db_models.CharField(
        max_length=200,
        blank=True,
        help_text='SEO标题（浏览器标题栏）'
    ))
    Product.add_to_class('seo_description', db_models.TextField(
        blank=True,
        help_text='SEO描述（搜索引擎摘要）'
    ))
    Product.add_to_class('seo_keywords', db_models.CharField(
        max_length=500,
        blank=True,
        help_text='SEO关键词（逗号分隔）'
    ))
    
    # 营销相关
    Product.add_to_class('tagline', db_models.CharField(
        max_length=200,
        blank=True,
        help_text='产品标语（简短卖点）'
    ))
    Product.add_to_class('key_benefits', db_models.JSONField(
        default=list,
        blank=True,
        help_text='核心价值点（JSON数组）'
    ))
    Product.add_to_class('target_industries', db_models.JSONField(
        default=list,
        blank=True,
        help_text='目标行业（JSON数组）'
    ))
    
    # 统计相关
    Product.add_to_class('view_count', db_models.PositiveIntegerField(
        default=0,
        help_text='浏览次数'
    ))
    Product.add_to_class('download_count', db_models.PositiveIntegerField(
        default=0,
        help_text='资料下载次数'
    ))
    
    # 时间相关
    Product.add_to_class('portal_published_at', db_models.DateTimeField(
        null=True,
        blank=True,
        help_text='门户上线时间'
    ))