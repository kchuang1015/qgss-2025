#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
自動生成的 Markdown 文件清理腳本
'''

import os
from pathlib import Path
from datetime import datetime

def cleanup_markdown_files():
    '''刪除不需要的 Markdown 文件'''
    root_dir = Path('/workspaces/qgss-2025')
    
    # 要刪除的文件列表
    files_to_delete = [
        'TRANSLATION_GUIDE.md',  # 翻譯工具使用指南，翻譯工作已完成，相關工具已清理
    ]
    
    deleted_count = 0
    failed_count = 0
    
    print("開始清理 Markdown 文件...")
    print("=" * 80)
    
    for file_path in files_to_delete:
        full_path = root_dir / file_path
        try:
            if full_path.exists():
                # 創建備份
                backup_path = full_path.with_suffix('.md.backup')
                full_path.rename(backup_path)
                print(f"✓ 已備份: {file_path} -> {backup_path.name}")
                
                # 刪除原文件（實際上是重命名為備份）
                # backup_path.unlink()  # 如果要真正刪除，取消註解這行
                deleted_count += 1
            else:
                print(f"⚠ 文件不存在: {file_path}")
        except Exception as e:
            print(f"✗ 刪除失敗: {file_path} - {e}")
            failed_count += 1
    
    print("=" * 80)
    print(f"\n清理完成!")
    print(f"  已處理: {deleted_count} 個文件")
    print(f"  失敗: {failed_count} 個文件")
    print(f"\n注意: 文件已重命名為 .md.backup，如需恢復請重命名回 .md")
    print(f"      如需永久刪除，請手動刪除 .backup 文件")

if __name__ == '__main__':
    cleanup_markdown_files()
