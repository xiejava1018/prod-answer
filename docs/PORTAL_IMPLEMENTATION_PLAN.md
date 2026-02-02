# 📋 产品介绍门户实施规划文档

## 一、项目概述

### 1.1 项目背景
基于现有产品能力匹配系统，构建面向客户的产品介绍门户，展示产品功能、技术参数和解决方案，提升产品营销能力。

### 1.2 目标用户
- **外部客户**：了解产品功能、技术参数、应用场景
- **销售团队**：快速查找产品信息、生成对比报告
- **市场团队**：展示解决方案、客户案例

### 1.3 核心目标
- 打造专业、现代化的产品展示平台
- 提供直观的产品搜索、筛选、对比功能
- 支持多维度产品信息展示（功能、性能、安全等）
- 与现有匹配系统数据无缝对接

---

## 二、功能架构设计

### 2.1 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│                    产品介绍门户 (Frontend)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  门户首页    │  │  产品中心    │  │   解决方案      │  │
│  │  (Portal)   │  │  (Products) │  │  (Solutions)    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  产品对比    │  │  资源中心    │  │   关于我们      │  │
│  │  (Compare)  │  │  (Resources)│  │   (About)       │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                API网关层 (Backend API)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ 门户产品API │  │ 解决方案API │  │   对比分析API   │  │
│  │ (Portal)   │  │ (Solutions) │  │   (Compare)     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│              数据服务层 (Data Service)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ 产品数据    │  │ 功能特性    │  │   技术参数      │  │
│  │ (Products)  │  │ (Features)  │  │   (Metadata)    │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 功能模块详细设计

#### 模块一：门户首页 (Portal Home)
**路径**：`/portal`
**功能描述**：门户入口，展示产品价值主张和导航

**页面结构**：
- **Hero区域**（占屏60%）
  - 产品标语："智能安全产品能力匹配平台"
  - 价值主张："精准匹配 · 智能推荐 · 高效决策"
  - CTA按钮："探索产品"、"查看解决方案"
  
- **产品分类导航**
  - 资产测绘与攻击面管理
  - 互联网暴露面测绘运营
  - 安全大数据平台
  - 安全管理和自动化编排
  - 综合安全平台

- **热门产品推荐**（3-4个卡片）
  - 产品名称、厂商、简介
  - 核心功能标签
  - "查看详情"按钮

- **解决方案轮播**
  - 金融行业解决方案
  - 政府行业解决方案
  - 企业安全解决方案

- **快速统计**
  - 产品总数
  - 功能特性总数
  - 客户案例数

- **使用指南时间线**
  - 4步快速了解平台

**技术要点**：
- 响应式设计，支持PC/移动端
- 图片懒加载优化
- 轮播组件使用Swiper
- 骨架屏提升加载体验

---

#### 模块二：产品中心 (Product Center)
**路径**：`/portal/products`
**功能描述**：产品展示、搜索、筛选

**页面结构**：
- **筛选面板**（左侧，可折叠）
  - 子系统类型（多选）
  - 产品分类（多选）
  - 厂商（多选）
  - 指标类型（产品功能、性能、安全等）
  - 重要性等级（1-10滑块）

- **搜索栏**
  - 关键词搜索（产品名称、描述、功能）
  - 搜索建议（自动补全）

- **视图切换**
  - 卡片视图（默认，3列）
  - 列表视图（详细信息）

- **排序选项**
  - 最新发布
  - 名称（A-Z）
  - 功能数量
  - 自定义权重

- **产品卡片**（卡片视图）
  - 产品名称（大字体）
  - 版本号
  - 厂商
  - 子系统类型标签（彩色）
  - 产品描述（2行截断）
  - 核心功能预览（3个标签）
  - 技术参数元数据（关键指标）
  - "查看详情"按钮

- **产品列表项**（列表视图）
  - 产品名称+版本
  - 厂商+分类
  - 子系统类型
  - 功能数量
  - 操作按钮（查看、对比）

**技术要点**：
- 虚拟滚动优化（超过50个产品）
- 筛选条件URL同步（支持分享）
- 搜索防抖（300ms）
- 分页加载（每次20个）

---

#### 模块三：产品详情页 (Product Detail)
**路径**：`/portal/products/:id`
**功能描述**：展示完整产品信息

**页面结构**：
- **产品头部信息**
  - 产品名称（大标题）
  - 版本号
  - 厂商（带链接）
  - 子系统类型（彩色标签）
  - 分类
  - 更新时间

- **产品概述**
  - 产品描述（富文本）
  - 核心价值点（图标+文字）

- **技术参数元数据**（卡片式）
  - 性能指标
  - 系统要求
  - 部署方式
  - 许可证类型
  - 支持服务

- **功能特性列表**（树形结构）
  - 一级功能（可折叠）
    - 二级功能
      - 功能名称
      - 描述
      - 指标类型（标签）
      - 重要性等级（可视化：1-10星）

- **功能统计**
  - 总功能数
  - 各指标类型分布（饼图）
  - 重要性等级分布（柱状图）

- **相关产品推荐**
  - 同子系统类型产品
  - 同厂商其他产品
  - 功能相似产品（基于嵌入向量）

- **操作按钮**
  - "加入对比"
  - "下载资料"
  - "申请试用"
  - "联系销售"

**技术要点**：
- 功能树懒加载
- 图表使用ECharts
- 嵌入向量计算相关产品（余弦相似度）
- 页面分享功能（Open Graph协议）

---

#### 模块四：产品对比 (Product Compare)
**路径**：`/portal/compare`
**功能描述**：多产品对比分析

**页面结构**：
- **产品选择器**
  - 最多选择4个产品
  - 搜索添加产品
  - 已选产品标签（可删除）

- **对比维度选择**
  - 基本信息
  - 功能特性
  - 技术参数
  - 子系统类型

- **对比表格**
  - 行：对比项
  - 列：产品（2-4列）
  - 差异高亮（不同值标红）
  - 相同值合并显示

- **功能对比详情**
  - 共同功能（交集）
  - 独有功能（差集）
  - 功能覆盖度（百分比）

- **可视化对比**
  - 雷达图（多维度评分）
  - 柱状图（功能数量对比）
  - 词云（功能关键词）

- **导出功能**
  - 导出PDF报告
  - 导出Excel表格
  - 分享对比链接

**技术要点**：
- 对比数据前端缓存（localStorage）
- 差异算法（文本相似度）
- PDF生成（jsPDF）
- 响应式表格（横向滚动）

---

#### 模块五：解决方案中心 (Solutions)
**路径**：`/portal/solutions`
**功能描述**：行业解决方案展示

**页面结构**：
- **解决方案分类**
  - 按行业（金融、政府、企业、医疗、教育）
  - 按场景（安全运营、威胁检测、合规审计）

- **解决方案卡片**
  - 解决方案名称
  - 适用行业/场景
  - 核心痛点
  - 解决方案概述
  - 关联产品数量
  - 客户案例数

- **解决方案详情页** (`/portal/solutions/:id`)
  - 行业背景与挑战
  - 解决方案架构图
  - 核心功能模块
  - 关联产品列表（带链接）
  - 客户成功案例
  - 实施效果数据
  - 咨询按钮

**技术要点**：
- 解决方案与产品多对多关联
- 架构图使用SVG或图片
- 案例数据可视化

---

#### 模块六：资源中心 (Resources)
**路径**：`/portal/resources`
**功能描述**：产品资料下载

**页面结构**：
- **资源分类**
  - 产品文档（用户手册、安装指南）
  - 白皮书（技术、行业）
  - 案例研究（客户成功故事）
  - 视频教程（产品演示、操作指南）

- **资源列表**
  - 资源标题
  - 类型图标
  - 文件大小
  - 下载次数
  - 上传日期
  - 下载按钮（需填写表单）

- **下载表单**
  - 姓名
  - 公司
  - 职位
  - 邮箱
  - 电话
  - 用途说明

**技术要点**：
- 文件存储（OSS/S3）
  - 下载权限控制
  - 下载统计
  - 表单验证

---

#### 模块七：关于我们 (About)
**路径**：`/portal/about`
**功能描述**：公司信息展示

**页面结构**：
- **公司简介**
  - 公司使命、愿景、价值观
  - 发展历程（时间线）
  - 核心团队

- **联系我们**
  - 地址、电话、邮箱
  - 在线地图
  - 联系表单

- **新闻动态**
  - 公司新闻
  - 产品更新
  - 行业洞察

---

### 2.3 数据模型扩展

#### 扩展现有模型

```python
# apps/products/models.py

class Product(models.Model):
    # 现有字段...
    
    # === 新增门户相关字段 ===
    
    # 门户展示相关
    is_featured = models.BooleanField(
        default=False, 
        help_text='是否推荐产品（门户首页展示）'
    )
    sort_weight = models.IntegerField(
        default=0, 
        help_text='排序权重（值越大越靠前）'
    )
    thumbnail = models.ImageField(
        upload_to='product_thumbnails/%Y/%m/',
        blank=True,
        help_text='产品缩略图（建议尺寸：400x300）'
    )
    banner_image = models.ImageField(
        upload_to='product_banners/%Y/%m/',
        blank=True,
        help_text='产品横幅图（建议尺寸：1200x400）'
    )
    
    # SEO相关
    seo_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='SEO标题（浏览器标题栏）'
    )
    seo_description = models.TextField(
        blank=True,
        help_text='SEO描述（搜索引擎摘要）'
    )
    seo_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text='SEO关键词（逗号分隔）'
    )
    
    # 营销相关
    tagline = models.CharField(
        max_length=200,
        blank=True,
        help_text='产品标语（简短卖点）'
    )
    key_benefits = models.JSONField(
        default=list,
        blank=True,
        help_text='核心价值点（JSON数组）'
    )
    target_industries = models.JSONField(
        default=list,
        blank=True,
        help_text='目标行业（JSON数组）'
    )
    
    # 统计相关
    view_count = models.PositiveIntegerField(
        default=0,
        help_text='浏览次数'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        help_text='资料下载次数'
    )
    
    # 状态相关
    is_on_portal = models.BooleanField(
        default=True,
        help_text='是否在门户展示'
    )
    portal_published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='门户上线时间'
    )
    
    class Meta:
        indexes = [
            # 现有索引...
            
            # 新增门户优化索引
            models.Index(
                fields=['is_on_portal', 'is_active', 'sort_weight', '-created_at'],
                name='idx_portal_display'
            ),
            models.Index(
                fields=['is_featured', 'is_on_portal', '-portal_published_at'],
                name='idx_featured_products'
            ),
            models.Index(
                fields=['subsystem_type', 'is_on_portal', 'sort_weight'],
                name='idx_subsystem_display'
            ),
        ]
```

#### 新增模型

```python
# apps/portal/models.py

class Solution(models.Model):
    """解决方案模型"""
    
    SOLUTION_TYPE_CHOICES = [
        ('industry', '按行业'),
        ('scenario', '按场景'),
        ('use_case', '按用例'),
    ]
    
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
        verbose_name = 'Solution'
        verbose_name_plural = 'Solutions'
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
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
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
        verbose_name = 'Portal View Log'
        verbose_name_plural = 'Portal View Logs'
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
```

---

### 2.4 API设计

#### 门户产品API

```python
# apps/portal/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Product, Solution, Resource
from .serializers import (
    PortalProductSerializer,
    PortalProductDetailSerializer,
    PortalSolutionSerializer,
    PortalResourceSerializer,
)


class PortalProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    门户产品API（只读）
    """
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
        'features__feature_name',
        'features__description',
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
        if self.action == 'retrieve':
            return PortalProductDetailSerializer
        return super().get_serializer_class()
    
    def retrieve(self, request, *args, **kwargs):
        """获取产品详情，并增加浏览次数"""
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
        """获取推荐产品"""
        featured_products = self.get_queryset().filter(
            is_featured=True
        )[:8]
        
        serializer = self.get_serializer(featured_products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """
        产品对比
        POST /api/v1/portal/products/compare/
        Body: { product_ids: [uuid1, uuid2, uuid3] }
        """
        product_ids = request.data.get('product_ids', [])
        
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
        
        products = self.get_queryset().filter(id__in=product_ids)
        
        if products.count() < 2:
            return Response(
                {'error': '有效产品数量不足2个'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用特殊序列化器进行对比
        from .serializers import PortalProductCompareSerializer
        serializer = PortalProductCompareSerializer(products, many=True)
        
        return Response({
            'count': products.count(),
            'products': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取产品统计信息"""
        queryset = self.get_queryset()
        
        stats = {
            'total_products': queryset.count(),
            'total_features': sum(p.features.filter(is_active=True).count() for p in queryset),
            'subsystem_types': queryset.values('subsystem_type').annotate(
                count=models.Count('id')
            ),
            'categories': queryset.values('category').annotate(
                count=models.Count('id')
            ),
            'vendors': queryset.values('vendor').annotate(
                count=models.Count('id')
            ),
        }
        
        return Response(stats)
    
    def _log_view(self, instance):
        """记录访问日志"""
        from .models import PortalViewLog
        
        # 获取IP地址
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')
        
        # 获取User-Agent
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        # 获取Referer
        referer = self.request.META.get('HTTP_REFERER', '')
        
        # 创建日志记录
        PortalViewLog.objects.create(
            content_type='product',
            object_id=instance.id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
        )


class PortalSolutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    解决方案API（只读）
    """
    queryset = Solution.objects.filter(is_active=True)
    serializer_class = PortalSolutionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'solution_type': ['exact', 'in'],
        'category': ['exact', 'in'],
        'is_featured': ['exact'],
    }
    
    search_fields = ['name', 'summary', 'pain_points']
    
    ordering_fields = ['sort_weight', 'published_at', 'created_at']
    ordering = ['-sort_weight', '-published_at']
    
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
        return Response(serializer.data)


class PortalResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    资源中心API（只读）
    """
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = PortalResourceSerializer
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
        return Response({
            'download_url': request.build_absolute_uri(resource.file.url),
            'file_name': resource.file.name.split('/')[-1],
            'file_size': resource.file_size,
        })
```

---

### 2.5 前端架构设计

#### 技术栈

```json
{
  "dependencies": {
    "@vueuse/core": "^10.0.0",
    "swiper": "^11.0.0",
    "vue-lazyload": "^3.0.0",
    "echarts": "^5.4.0",
    "vue-echarts": "^6.6.0",
    "jspdf": "^2.5.0",
    "html2canvas": "^1.4.0",
    "@element-plus/icons-vue": "^2.3.0"
  }
}
```

#### 目录结构

```
frontend/src/
├── views/
│   └── portal/
│       ├── Home.vue              # 门户首页
│       ├── ProductList.vue       # 产品列表
│       ├── ProductDetail.vue     # 产品详情
│       ├── ProductCompare.vue    # 产品对比
│       ├── SolutionList.vue      # 解决方案列表
│       ├── SolutionDetail.vue    # 解决方案详情
│       ├── ResourceList.vue      # 资源列表
│       └── About.vue             # 关于我们
│
├── components/portal/
│   ├── ProductCard.vue           # 产品卡片
│   ├── ProductFilter.vue         # 产品筛选器
│   ├── FeatureTree.vue           # 功能树
│   ├── CompareTable.vue          # 对比表格
│   ├── SolutionBanner.vue        # 解决方案横幅
│   └── ResourceItem.vue          # 资源项
│
├── api/
│   └── portal.ts                 # 门户API
│
├── types/
│   └── portal.ts                 # 门户类型定义
│
├── layouts/
│   └── PortalLayout.vue          # 门户布局
│
├── store/modules/
│   └── portal.ts                 # 门户状态管理
│
├── assets/portal/
│   ├── styles/                   # 门户专用样式
│   └── images/                   # 门户图片
│
└── router/
    └── portal.ts                 # 门户路由
```

---

### 2.6 性能优化策略

#### 后端优化

1. **数据库优化**
   - 添加复合索引（已在前述模型中定义）
   - 使用`select_related`和`prefetch_related`减少查询次数
   - 对频繁查询的字段添加缓存（Redis）

2. **缓存策略**
   ```python
   # 产品列表缓存（5分钟）
   @cache_page(60 * 5)
   def list(self, request, *args, **kwargs):
       return super().list(request, *args, **kwargs)
   
   # 产品详情缓存（1小时）
   @cache_page(60 * 60)
   def retrieve(self, request, *args, **kwargs):
       return super().retrieve(request, *args, **kwargs)
   ```

3. **分页优化**
   - 默认每页20条
   - 最大每页100条（防止恶意请求）
   - 使用`CursorPagination`提升大数据量性能

#### 前端优化

1. **代码分割**
   ```typescript
   // 路由懒加载
   const ProductDetail = () => import('@/views/portal/ProductDetail.vue')
   ```

2. **图片优化**
   - 使用WebP格式（兼容JPEG回退）
   - 图片懒加载（vue-lazyload）
   - 响应式图片（srcset）

3. **数据缓存**
   ```typescript
   // 使用Pinia缓存产品数据
   export const usePortalStore = defineStore('portal', {
     state: () => ({
       productCache: new Map(),
       categoryCache: null,
     }),
     actions: {
       async getProduct(id: string) {
         if (this.productCache.has(id)) {
           return this.productCache.get(id)
         }
         const product = await portalAPI.getProduct(id)
         this.productCache.set(id, product)
         return product
       },
     },
   })
   ```

4. **虚拟滚动**
   - 产品列表超过50项时使用虚拟滚动
   - 功能树超过100个节点时使用虚拟滚动

---

### 2.7 安全与权限

#### 访问控制

1. **IP限流**
   ```python
   # 每个IP每分钟最多访问100次
   'DEFAULT_THROTTLE_RATES': {
       'portal': '100/min',
   }
   ```

2. **敏感信息过滤**
   ```python
   # PortalProductSerializer中排除敏感字段
   class Meta:
       exclude = ['spec_metadata', 'internal_notes']
   ```

3. **下载权限**
   - 资源下载需要填写表单
   - 表单数据验证（邮箱、电话格式）
   - 下载链接添加过期时间（30分钟）

#### 数据保护

1. **日志脱敏**
   - IP地址部分隐藏（如：192.168.x.x）
   - User-Agent只记录浏览器类型

2. **GDPR合规**
   - 提供数据导出功能
   - 提供数据删除功能
   - 明确的隐私政策链接

---

### 2.8 部署与监控

#### 部署架构

```
┌─────────────────────────────────────────┐
│          CDN (Static Assets)            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Load Balancer (Nginx)         │
└────────┬──────────────────┬────────────┘
         │                  │
┌────────▼──────┐    ┌─────▼────────┐
│  Web Server 1 │    │  Web Server 2 │
│   (Gunicorn)  │    │   (Gunicorn)  │
└────────┬──────┘    └─────┬────────┘
         │                  │
┌────────▼──────────────────▼────────────┐
│         Database (PostgreSQL)          │
│   ┌──────────────────────────────────┐  │
│   │  pgvector (Embedding Storage)  │  │
│   └──────────────────────────────────┘  │
└──────────────────────────────────────────┘
         │
┌────────▼──────────────┐
│   Redis (Cache/Queue)  │
└────────────────────────┘
```

#### 监控指标

1. **业务指标**
   - 页面PV/UV
   - 产品浏览量Top10
   - 搜索关键词统计
   - 下载转化率

2. **性能指标**
   - API响应时间（P95, P99）
   - 数据库查询时间
   - 缓存命中率
   - 错误率

3. **告警规则**
   - 错误率 > 1%（5分钟内）
   - 平均响应时间 > 500ms（5分钟内）
   - 数据库连接数 > 80%

---

### 2.9 测试计划

#### 单元测试

```python
# apps/portal/tests/test_views.py

class PortalProductViewSetTestCase(APITestCase):
    def setUp(self):
        self.product = ProductFactory.create(is_on_portal=True)
        
    def test_list_products(self):
        response = self.client.get('/api/v1/portal/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        
    def test_retrieve_product(self):
        response = self.client.get(f'/api/v1/portal/products/{self.product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], self.product.name)
        
    def test_product_view_count(self):
        initial_count = self.product.view_count
        self.client.get(f'/api/v1/portal/products/{self.product.id}/')
        self.product.refresh_from_db()
        self.assertEqual(self.product.view_count, initial_count + 1)
```

#### 集成测试

```python
# apps/portal/tests/test_integration.py

class PortalIntegrationTestCase(APITestCase):
    def test_product_compare_flow(self):
        # 创建测试产品
        products = ProductFactory.create_batch(3, is_on_portal=True)
        
        # 发起对比请求
        response = self.client.post(
            '/api/v1/portal/products/compare/',
            {'product_ids': [str(p.id) for p in products]},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['products']), 3)
        
    def test_solution_product_relationship(self):
        solution = SolutionFactory.create()
        products = ProductFactory.create_batch(2, is_on_portal=True)
        solution.products.add(*products)
        
        response = self.client.get(f'/api/v1/portal/solutions/{solution.id}/')
        self.assertEqual(len(response.data['products']), 2)
```

#### 前端测试

```typescript
// frontend/src/views/portal/__tests__/ProductList.spec.ts

import { mount } from '@vue/test-utils'
import ProductList from '../ProductList.vue'
import { createTestingPinia } from '@pinia/testing'

describe('ProductList', () => {
  it('renders product cards', async () => {
    const wrapper = mount(ProductList, {
      global: {
        plugins: [createTestingPinia()],
      },
    })
    
    await flushPromises()
    
    expect(wrapper.findAll('.product-card')).toHaveLength(2)
  })
  
  it('filters products by category', async () => {
    const wrapper = mount(ProductList, {
      global: {
        plugins: [createTestingPinia()],
      },
    })
    
    await wrapper.find('[data-test="filter-category"]').setValue('security')
    await wrapper.find('[data-test="apply-filter"]').trigger('click')
    
    expect(wrapper.vm.filteredProducts).toHaveLength(1)
  })
})
```

---

### 2.10 文档与培训

#### 技术文档

1. **API文档**（自动生成）
   ```bash
   # 使用drf-spectacular生成OpenAPI文档
   python manage.py spectacular --file openapi.yml
   ```

2. **部署文档**
   - 环境要求
   - 安装步骤
   - 配置说明
   - 常见问题

3. **维护手册**
   - 日常监控
   - 备份恢复
   - 性能调优
   - 故障排查

#### 用户培训

1. **管理员培训**
   - 产品上架流程
   - 解决方案配置
   - 资源上传管理
   - 数据分析报表

2. **销售培训**
   - 门户功能介绍
   - 产品查询技巧
   - 对比报告生成
   - 客户演示流程

---

## 三、实施路线图

### 第一阶段：核心功能开发（2周）

**目标**：完成门户基础框架和核心功能

**任务清单**：
- [ ] Day 1-2: 项目初始化，创建Django App和Vue模块
- [ ] Day 3-4: 数据模型扩展（Product、Solution、Resource）
- [ ] Day 5-6: 后端API开发（Product ViewSet）
- [ ] Day 7-8: 前端基础布局（Header、Footer、导航）
- [ ] Day 9-10: 产品列表页开发（筛选、搜索、分页）
- [ ] Day 11-12: 产品详情页开发（信息展示、功能树）
- [ ] Day 13-14: 联调测试，Bug修复

**交付物**：
- 可运行的产品列表和详情页
- 基础API文档
- 单元测试覆盖率 > 80%

---

### 第二阶段：增强功能开发（1周）

**目标**：完成产品对比和解决方案功能

**任务清单**：
- [ ] Day 1: 产品对比API开发
- [ ] Day 2: 产品对比前端页面（选择、表格、可视化）
- [ ] Day 3: 解决方案模型和API
- [ ] Day 4: 解决方案列表和详情页
- [ ] Day 5: 资源中心基础功能

**交付物**：
- 产品对比功能（支持2-4个产品）
- 解决方案展示页面
- 资源上传和下载功能

---

### 第三阶段：门户首页和优化（1周）

**目标**：完成门户首页和性能优化

**任务清单**：
- [ ] Day 1: 门户首页UI设计（Hero区域、导航、推荐）
- [ ] Day 2: 首页数据接口和动态内容
- [ ] Day 3: 响应式适配（移动端优化）
- [ ] Day 4: 性能优化（缓存、懒加载、虚拟滚动）
- [ ] Day 5: SEO优化（Meta标签、结构化数据）

**交付物**：
- 完整的门户首页
- 响应式支持的移动端
- 性能指标（Lighthouse评分 > 90）

---

### 第四阶段：测试和部署（3天）

**目标**：完成全面测试和生产环境部署

**任务清单**：
- [ ] Day 1: 集成测试和Bug修复
- [ ] Day 2: 生产环境部署和配置
- [ ] Day 3: 监控告警配置和文档整理

**交付物**：
- 生产环境可访问的门户
- 完整的测试报告
- 部署文档和操作手册

---

## 四、资源需求

### 人力资源

| 角色 | 人数 | 职责 |
|------|------|------|
| 后端开发工程师 | 1人 | Django API开发、数据库设计 |
| 前端开发工程师 | 1人 | Vue 3前端开发、UI实现 |
| UI/UX设计师 | 0.5人 | 界面设计、交互设计（可兼职） |
| 测试工程师 | 0.5人 | 测试用例编写、Bug跟踪（可兼职） |
| DevOps工程师 | 0.5人 | 部署、监控配置（可兼职） |

### 技术资源

| 资源 | 规格 | 用途 |
|------|------|------|
| 开发服务器 | 4核8G内存 | 开发环境 |
| 测试服务器 | 4核8G内存 | 测试环境 |
| 生产服务器 | 8核16G内存 | 生产环境 |
| PostgreSQL | 12+版本 | 主数据库 |
| Redis | 6+版本 | 缓存和队列 |
| CDN | 100GB流量/月 | 静态资源加速 |
| 对象存储 | 50GB空间 | 文件存储 |

### 软件许可

- Django REST Framework（开源）
- Vue 3（开源）
- Element Plus（开源）
- ECharts（开源）
- Redis（开源）
- PostgreSQL（开源）

---

## 五、风险评估与应对

### 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 嵌入向量计算性能瓶颈 | 中 | 高 | 使用缓存+异步任务，优化算法 |
| 数据库查询慢 | 中 | 中 | 添加索引、使用读写分离 |
| 第三方库兼容性问题 | 低 | 中 | 锁定版本号、提前测试 |

### 项目管理风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 需求变更 | 中 | 中 | 建立变更流程、预留缓冲时间 |
| 人员变动 | 低 | 高 | 代码审查、文档完善、知识共享 |
| 时间延期 | 中 | 中 | 每日站会、周进度评审、风险预警 |

---

## 六、成功标准

### 功能指标

- [ ] 所有页面功能正常，无严重Bug
- [ ] API响应时间 < 200ms（P95）
- [ ] 前端页面加载时间 < 3秒（3G网络）
- [ ] 支持主流浏览器（Chrome、Firefox、Safari、Edge）

### 业务指标

- [ ] 产品信息完整度 > 95%
- [ ] 搜索准确率 > 90%
- [ ] 用户满意度 > 4.5/5.0

### 技术指标

- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖率 > 70%
- [ ] 性能测试通过率 > 95%
- [ ] 安全扫描无高危漏洞

---

## 七、后续迭代计划

### 短期（1-2个月）

- [ ] 用户行为分析（热力图、漏斗分析）
- [ ] 智能推荐（基于浏览历史）
- [ ] 多语言支持（英文版）

### 中期（3-6个月）

- [ ] 客户评价系统
- [ ] 在线客服集成
- [ ] 产品视频展示
- [ ] AR/VR产品演示

### 长期（6个月以上）

- [ ] 社区论坛
- [ ] 开发者中心
- [ ] 合作伙伴门户
- [ ] 国际化部署

---

**文档版本**：v1.0  
**创建日期**：2026-01-31  
**创建人**：AI Assistant  
**最后更新**：2026-01-31
