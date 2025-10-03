#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 文件分析與清理建議腳本
分析專案中的 .md 文件並提供清理建議
"""

import os
from pathlib import Path
from datetime import datetime

def get_file_info(filepath):
    """獲取文件信息"""
    stats = os.stat(filepath)
    return {
        'size': stats.st_size,
        'modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'lines': sum(1 for _ in open(filepath, 'r', encoding='utf-8'))
    }

def analyze_markdown_files():
    """分析所有 Markdown 文件"""
    root_dir = Path('/workspaces/qgss-2025')
    md_files = list(root_dir.rglob('*.md'))
    
    print("=" * 80)
    print("Markdown 文件分析報告")
    print("=" * 80)
    print(f"掃描目錄: {root_dir}")
    print(f"找到文件數: {len(md_files)}")
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    analysis_results = []
    
    for md_file in sorted(md_files):
        rel_path = md_file.relative_to(root_dir)
        info = get_file_info(md_file)
        
        # 讀取文件前幾行來判斷內容
        with open(md_file, 'r', encoding='utf-8') as f:
            first_lines = [f.readline().strip() for _ in range(5)]
            content_preview = '\n'.join(first_lines)
        
        # 判斷文件用途和建議
        filename = md_file.name
        if filename == 'README.md':
            if 'qgss-2025' in content_preview or 'Qiskit Global Summer School' in content_preview:
                # 根目錄的 README.md
                status = '✓ 必要保留'
                reason = '專案主要說明文件，介紹 QGSS 2025 課程和使用方式'
                action = 'keep'
            else:
                # 子目錄的 README.md
                status = '✓ 必要保留'
                reason = f'子專案說明文件 ({rel_path.parent})'
                action = 'keep'
        elif filename == 'TRANSLATION_GUIDE.md':
            status = '✗ 建議刪除'
            reason = '翻譯工具使用指南，翻譯工作已完成，相關工具已清理'
            action = 'delete'
        elif filename == 'TRANSLATION_SUMMARY.md':
            status = '? 可選保留'
            reason = '翻譯完成摘要，可作為工作記錄但非必需'
            action = 'optional'
        else:
            status = '? 需檢查'
            reason = '未知用途的文件'
            action = 'check'
        
        analysis_results.append({
            'path': str(rel_path),
            'filename': filename,
            'info': info,
            'status': status,
            'reason': reason,
            'action': action,
            'preview': content_preview
        })
    
    # 按動作分組顯示
    print("\n📋 分析結果摘要\n")
    
    actions = {'keep': [], 'delete': [], 'optional': [], 'check': []}
    for result in analysis_results:
        actions[result['action']].append(result)
    
    # 必要保留的文件
    print("✓ 必要保留的文件 (KEEP)")
    print("-" * 80)
    for result in actions['keep']:
        print(f"\n📄 {result['path']}")
        print(f"   大小: {result['info']['size']:,} bytes | 行數: {result['info']['lines']} | 修改: {result['info']['modified']}")
        print(f"   原因: {result['reason']}")
    
    # 建議刪除的文件
    print("\n" + "=" * 80)
    print("\n✗ 建議刪除的文件 (DELETE)")
    print("-" * 80)
    for result in actions['delete']:
        print(f"\n📄 {result['path']}")
        print(f"   大小: {result['info']['size']:,} bytes | 行數: {result['info']['lines']} | 修改: {result['info']['modified']}")
        print(f"   原因: {result['reason']}")
    
    # 可選保留的文件
    print("\n" + "=" * 80)
    print("\n? 可選保留的文件 (OPTIONAL)")
    print("-" * 80)
    for result in actions['optional']:
        print(f"\n📄 {result['path']}")
        print(f"   大小: {result['info']['size']:,} bytes | 行數: {result['info']['lines']} | 修改: {result['info']['modified']}")
        print(f"   原因: {result['reason']}")
    
    # 統計
    print("\n" + "=" * 80)
    print("\n📊 統計摘要")
    print("-" * 80)
    print(f"總文件數: {len(md_files)}")
    print(f"  ✓ 必要保留: {len(actions['keep'])} 個")
    print(f"  ✗ 建議刪除: {len(actions['delete'])} 個")
    print(f"  ? 可選保留: {len(actions['optional'])} 個")
    print(f"  ? 需檢查: {len(actions['check'])} 個")
    
    return actions

def generate_cleanup_script(actions):
    """生成清理腳本"""
    script_content = """#!/usr/bin/env python3
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
"""
    
    for result in actions['delete']:
        script_content += f"        '{result['path']}',  # {result['reason']}\n"
    
    script_content += """    ]
    
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
    print(f"\\n清理完成!")
    print(f"  已處理: {deleted_count} 個文件")
    print(f"  失敗: {failed_count} 個文件")
    print(f"\\n注意: 文件已重命名為 .md.backup，如需恢復請重命名回 .md")
    print(f"      如需永久刪除，請手動刪除 .backup 文件")

if __name__ == '__main__':
    cleanup_markdown_files()
"""
    
    return script_content

if __name__ == '__main__':
    actions = analyze_markdown_files()
    
    # 生成清理腳本
    if actions['delete']:
        print("\n" + "=" * 80)
        print("\n🔧 生成清理腳本")
        print("-" * 80)
        script_content = generate_cleanup_script(actions)
        script_path = Path('/workspaces/qgss-2025/cleanup_markdown.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"已生成清理腳本: {script_path}")
        print("\n執行方式:")
        print(f"  python3 {script_path}")
        print("\n注意: 腳本會將文件重命名為 .backup 而非直接刪除，以便恢復")
    
    print("\n" + "=" * 80)
    print("\n✅ 分析完成")
    print("=" * 80)