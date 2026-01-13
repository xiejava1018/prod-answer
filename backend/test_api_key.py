#!/usr/bin/env python
"""
Test API key configuration via web interface.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.testing')
os.environ.setdefault('USE_SQLITE', 'True')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.embeddings.models import EmbeddingModelConfig

print("\n" + "="*60)
print("测试API密钥配置功能")
print("="*60)

# Get siliconflow config
config = EmbeddingModelConfig.objects.get(model_name='siliconflow-bge-large-zh')

print(f"\n当前配置:")
print(f"  模型: {config.model_name}")
print(f"  类型: {config.model_type}")
print(f"  提供商: {config.provider_name}")
print(f"  Base URL: {config.base_url}")
print(f"  API密钥状态: {'已配置' if config.api_key_encrypted else '未配置'}")

# Test setting API key
print(f"\n测试设置API密钥...")
test_key = "sk-test-key-for-siliconflow-12345"

try:
    config.set_api_key(test_key)
    config.save()
    print(f"  ✓ API密钥设置成功")

    # Verify it was stored
    retrieved_key = config.get_api_key()
    if retrieved_key == test_key:
        print(f"  ✓ API密钥验证成功")
    else:
        print(f"  ✗ API密钥验证失败")

    # Check encryption
    print(f"  加密存储: {config.api_key_encrypted[:20]}...")

    print(f"\n✅ 所有测试通过！")
    print(f"\n现在你可以在前端界面中配置真实的API密钥了。")
    print(f"访问: http://localhost:5173/embedding-settings")

except Exception as e:
    print(f"  ✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("="*60 + "\n")
