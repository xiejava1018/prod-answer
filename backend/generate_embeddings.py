"""
Generate embeddings for all features
"""
import os
import django
import sys

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.supabase')
django.setup()

from apps.products.models import Feature, FeatureEmbedding
from apps.embeddings.models import EmbeddingModelConfig
from apps.embeddings.services import EmbeddingServiceFactory


def generate_all_embeddings():
    """为所有特征生成向量嵌入"""

    # Get default config
    config = EmbeddingModelConfig.objects.filter(is_default=True).first()
    if not config:
        print("[ERROR] 没有找到默认的嵌入模型配置")
        print("[INFO] 请先在 Django Admin 中创建并激活一个嵌入模型配置")
        return

    print(f"[INFO] 使用嵌入模型: {config.model_name}")
    print(f"[INFO] 向量维度: {config.dimension}")
    print(f"[INFO] 提供商: {config.provider}")

    # Get embedding service
    try:
        service = EmbeddingServiceFactory.get_service()
        print("[OK] 嵌入服务初始化成功\n")
    except Exception as e:
        print(f"[ERROR] 嵌入服务初始化失败: {e}")
        return

    # Get all features without embeddings
    features = Feature.objects.all()
    total = features.count()

    print(f"[INFO] 总特征数: {total}")

    # Check existing embeddings
    existing_count = FeatureEmbedding.objects.count()
    print(f"[INFO] 已有嵌入数: {existing_count}")

    if existing_count > 0:
        print("\n[WARNING] 检测到已有嵌入数据")
        response = input("是否清除并重新生成? (y/N): ")
        if response.lower() == 'y':
            FeatureEmbedding.objects.all().delete()
            print("[OK] 已清除现有嵌入")
        else:
            print("[INFO] 将跳过已有嵌入的特征")

    print("\n" + "="*60)
    print("开始生成向量嵌入")
    print("="*60 + "\n")

    success_count = 0
    error_count = 0
    skip_count = 0

    # Process features in batches
    batch_size = 10
    texts = []
    feature_ids = []

    for idx, feature in enumerate(features, 1):
        # Check if embedding already exists
        if FeatureEmbedding.objects.filter(feature=feature).exists():
            skip_count += 1
            continue

        # Prepare text for embedding
        # Combine feature name and description
        text = f"{feature.feature_name}。{feature.description or ''}"
        texts.append(text)
        feature_ids.append(feature.id)

        # Process batch
        if len(texts) >= batch_size or idx == total:
            try:
                # Generate embeddings for batch
                embeddings = service.encode(texts)

                # Save embeddings
                for feat_id, embedding in zip(feature_ids, embeddings):
                    FeatureEmbedding.objects.create(
                        feature_id=feat_id,
                        embedding=embedding.tolist(),
                        model_name=config.model_name,
                        model_id=str(config.id)
                    )

                success_count += len(embeddings)
                print(f"[OK] 批次完成: {success_count}/{total - skip_count} ({success_count*100//(total - skip_count) if total > skip_count else 0}%)")

                # Clear batch
                texts = []
                feature_ids = []

            except Exception as e:
                error_count += len(texts)
                print(f"[ERROR] 批次失败: {e}")
                texts = []
                feature_ids = []

    # Print summary
    print("\n" + "="*60)
    print("生成完成!")
    print("="*60)
    print(f"总数: {total}")
    print(f"成功: {success_count}")
    print(f"跳过: {skip_count}")
    print(f"失败: {error_count}")
    print(f"数据库中嵌入总数: {FeatureEmbedding.objects.count()}")
    print("="*60)


if __name__ == '__main__':
    print("="*60)
    print("特征向量嵌入生成工具")
    print("="*60)
    print()

    try:
        generate_all_embeddings()

        print("\n下一步:")
        print("1. 在前端查看产品特征")
        print("2. 测试语义匹配功能")
        print("3. 导入需求并运行匹配分析")

    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
