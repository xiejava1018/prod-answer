"""
Django management command to initialize default embedding configurations.
"""
from django.core.management.base import BaseCommand
from apps.embeddings.models import EmbeddingModelConfig
import os


class Command(BaseCommand):
    help = 'Initialize default embedding model configurations'

    def handle(self, *args, **options):
        """Execute the command."""

        # Configurations for different providers
        configs = [
            {
                'model_name': 'siliconflow-bge-large-zh',
                'model_type': 'openai-compatible',
                'provider': 'openai-compatible',
                'provider_name': 'siliconflow',
                'base_url': 'https://api.siliconflow.cn/v1',
                'dimension': 1024,
                'model_params': {
                    'model': 'BAAI/bge-large-zh-v1.5'
                },
                'is_active': True,
                'is_default': True,
                'description': '硅基流动 BGE中文大模型 (推荐)'
            },
            {
                'model_name': 'zhipuai-embedding-2',
                'model_type': 'openai-compatible',
                'provider': 'openai-compatible',
                'provider_name': 'zhipuai',
                'base_url': 'https://open.bigmodel.cn/api/paas/v4',
                'dimension': 1024,
                'model_params': {
                    'model': 'embedding-2'
                },
                'is_active': False,
                'is_default': False,
                'description': '智谱AI Embedding-2模型'
            },
            {
                'model_name': 'qwen-embedding-v1',
                'model_type': 'openai-compatible',
                'provider': 'openai-compatible',
                'provider_name': 'qwen',
                'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'dimension': 1536,
                'model_params': {
                    'model': 'text-embedding-v3'
                },
                'is_active': False,
                'is_default': False,
                'description': '阿里通义千问 Embedding模型'
            },
        ]

        for config_data in configs:
            description = config_data.pop('description', '')

            # Check if config already exists
            if EmbeddingModelConfig.objects.filter(model_name=config_data['model_name']).exists():
                self.stdout.write(
                    self.style.WARNING(f"Configuration '{config_data['model_name']}' already exists. Skipping...")
                )
                continue

            # Create configuration
            config = EmbeddingModelConfig(**config_data)
            config.save()

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created: {config_data['model_name']} - {description}")
            )

        self.stdout.write(
            self.style.SUCCESS('\n配置初始化完成！')
        )
        self.stdout.write('注意：请在设置中添加相应的API Key才能使用这些配置。')
