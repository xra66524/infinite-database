"""
将 data/rules/ 下的所有 MD 文件迁移到 参考_无限恐怖FX/ 目录，
同时删除原始 HTML 文件。
"""

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_MD = PROJECT_ROOT / "data" / "rules"
TARGET_DIR = PROJECT_ROOT / "参考_无限恐怖FX"


def delete_html_files(directory: Path):
    """递归删除指定目录下所有 .html 和 .htm 文件"""
    deleted = 0
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        if root_path.name.lower() in ('images', 'image'):
            continue
        for file in files:
            if file.lower().endswith(('.html', '.htm')):
                file_path = root_path / file
                file_path.unlink()
                deleted += 1
    return deleted


def copy_md_files(source: Path, target: Path):
    """将 source 下所有 .md 文件复制到 target 同名相对路径"""
    copied = 0
    for root, dirs, files in os.walk(source):
        root_path = Path(root)
        rel_path = root_path.relative_to(source)
        target_subdir = target / rel_path

        for file in files:
            if not file.lower().endswith('.md'):
                continue
            src_file = root_path / file
            dst_file = target_subdir / file
            target_subdir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied += 1
    return copied


def remove_empty_dirs(directory: Path):
    """删除空目录（从最深层开始）"""
    removed = 0
    for root, dirs, files in os.walk(directory, topdown=False):
        root_path = Path(root)
        if root_path == directory:
            continue
        try:
            remaining = list(root_path.iterdir())
            if not remaining:
                root_path.rmdir()
                removed += 1
        except (OSError, PermissionError):
            pass
    return removed


def main():
    print("=" * 60)
    print("迁移工具：HTML 删除 + MD 迁移")
    print("=" * 60)

    # 1. 删除原始 HTML 文件
    print("\n[1/3] 删除原始 HTML 文件...")
    deleted = delete_html_files(TARGET_DIR)
    print(f"  已删除 {deleted} 个 HTML 文件")

    # 2. 复制 MD 文件
    print("\n[2/3] 复制 MD 文件到参考目录...")
    copied = copy_md_files(SOURCE_MD, TARGET_DIR)
    print(f"  已复制 {copied} 个 MD 文件")

    # 3. 清理 data/rules 目录
    print("\n[3/3] 清理临时目录...")
    if SOURCE_MD.exists():
        shutil.rmtree(SOURCE_MD)
        print(f"  已删除临时目录: {SOURCE_MD}")

    data_dir = PROJECT_ROOT / "data"
    if data_dir.exists():
        remove_empty_dirs(data_dir)

    print(f"\n完成！所有规则文件已迁移到 {TARGET_DIR.resolve()}")


if __name__ == '__main__':
    main()
