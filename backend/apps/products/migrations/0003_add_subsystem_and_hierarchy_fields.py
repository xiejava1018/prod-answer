# Generated manually for subsystem support and hierarchy structure

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_feature_feature_code'),
    ]

    operations = [
        # Product模型新增字段
        migrations.AddField(
            model_name='product',
            name='subsystem_type',
            field=models.CharField(
                max_length=50,
                blank=True,
                null=True,
                db_index=True,
                help_text='子系统类型',
                choices=[
                    ('asset_mapping', '资产测绘与攻击面管理子系统'),
                    ('exposure_mapping', '互联网暴露面测绘运营子系统'),
                    ('big_data', '安全大数据平台子系统'),
                    ('soar', '安全管理和自动化编排子系统'),
                    ('integrated', '综合安全平台'),
                    ('other', '其他'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='spec_metadata',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='技术参数元数据'
            ),
        ),
        # Feature模型新增字段
        migrations.AddField(
            model_name='feature',
            name='level1_function',
            field=models.CharField(
                max_length=200,
                blank=True,
                db_index=True,
                help_text='一级功能（用于层级结构）'
            ),
        ),
        migrations.AddField(
            model_name='feature',
            name='level2_function',
            field=models.CharField(
                max_length=200,
                blank=True,
                db_index=True,
                help_text='二级功能（用于层级结构）'
            ),
        ),
        migrations.AddField(
            model_name='feature',
            name='indicator_type',
            field=models.CharField(
                max_length=50,
                blank=True,
                db_index=True,
                help_text='指标项类型',
                choices=[
                    ('product_function', '产品功能'),
                    ('performance', '性能指标'),
                    ('security', '安全要求'),
                    ('reliability', '可靠性'),
                    ('compatibility', '兼容性'),
                    ('usability', '易用性'),
                    ('other', '其他'),
                ]
            ),
        ),
    ]
