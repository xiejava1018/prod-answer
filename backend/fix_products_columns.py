#!/usr/bin/env python
"""
修复产品表缺失的列
"""
import os
import sys
import django

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.db import connection

def add_missing_columns():
    with connection.cursor() as cursor:
        # 检查现有列
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'products'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"现有列: {existing_columns}")

        # 要添加的列
        columns_to_add = [
            ('is_featured', 'boolean DEFAULT false'),
            ('is_on_portal', 'boolean DEFAULT false'),
            ('view_count', 'integer DEFAULT 0'),
            ('download_count', 'integer DEFAULT 0'),
            ('sort_weight', 'integer DEFAULT 0'),
            ('tagline', "varchar(500) DEFAULT ''"),
            ('key_benefits', "jsonb DEFAULT '[]'"),
            ('target_industries', "jsonb DEFAULT '[]'"),
            ('seo_title', "varchar(200) DEFAULT ''"),
            ('seo_description', "text DEFAULT ''"),
            ('seo_keywords', "varchar(500) DEFAULT ''"),
            ('banner_image', "varchar(255) DEFAULT ''"),
            ('thumbnail', "varchar(255) DEFAULT ''"),
        ]

        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE products ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                print(f"添加列: {col_name}")
                cursor.execute(sql)
            else:
                print(f"列 {col_name} 已存在")

        # 添加 portal_published_at 列
        if 'portal_published_at' not in existing_columns:
            print("添加列: portal_published_at")
            cursor.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS portal_published_at timestamp NULL")

        print("\n所有列添加成功!")

if __name__ == '__main__':
    add_missing_columns()
