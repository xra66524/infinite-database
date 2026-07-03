"""
无限恐怖FX 规则提取脚本
将 参考_无限恐怖FX/ 下的所有 HTML 文件转换为 Markdown 格式
保存到 data/ 目录，保持相同的目录结构
"""

import os
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_ROOT / "参考_无限恐怖FX"
OUTPUT_DIR = PROJECT_ROOT / "data" / "rules"


def expand_hidden_divs(soup: BeautifulSoup):
    """展开所有隐藏的 div 内容（isHidden 模式）"""
    for div in soup.find_all('div', style=True):
        style = div.get('style', '')
        if 'display:none' in style.replace(' ', ''):
            div['style'] = style.replace('display:none', 'display:block').replace('display: none', 'display:block')
    
    # 移除 onclick 属性中 isHidden 相关的
    for elem in soup.find_all(attrs={"onclick": True}):
        onclick = elem.get('onclick', '')
        if 'isHidden' in onclick:
            del elem['onclick']
            if elem.get('style'):
                elem['style'] = elem['style'].replace('cursor:hand', '').strip()
                if not elem['style']:
                    del elem['style']
    
    return soup


def extract_title(soup: BeautifulSoup) -> str:
    """从 HTML 中提取标题"""
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""


def element_to_markdown(element, pending_newlines: int = 1) -> tuple[str, int]:
    """
    将 BeautifulSoup 元素递归转换为 Markdown 字符串。
    返回 (markdown_text, trailing_newlines) — trailing_newlines 表示结尾有多少个换行待处理。
    """
    if isinstance(element, Comment):
        return ('', 0)
    
    if isinstance(element, NavigableString):
        text = str(element)
        # 如果只有空白，返回空
        if not text.strip():
            # 保留单个空格用于内联
            if text == ' ':
                return (' ', 0)
            return ('', 0)
        return (text, 0)
    
    if not isinstance(element, Tag):
        return ('', 0)
    
    tag_name = element.name.lower()
    
    # 跳过 script, style, meta, head, title
    if tag_name in ('script', 'style', 'meta', 'head', 'title'):
        return ('', 0)
    
    # 处理 br 标签
    if tag_name == 'br':
        return ('\n', 1)
    
    # 处理 hr 标签
    if tag_name == 'hr':
        return ('\n\n---\n\n', 2)
    
    # 处理 p 标签
    if tag_name == 'p':
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        content = ''.join(parts).strip()
        if content:
            return (f'\n\n{content}\n\n', 2)
        return ('', 0)
    
    # 处理 b/strong 标签
    if tag_name in ('b', 'strong'):
        parts = []
        trailing = 0
        for child in element.children:
            text, t = element_to_markdown(child, 0)
            parts.append(text)
            trailing = t
        text = ''.join(parts).strip()
        if text:
            result = f'**{text}**'
            if trailing:
                result += '\n' * trailing
            return (result, trailing)
        return ('', 0)
    
    # 处理 i/em 标签
    if tag_name in ('i', 'em'):
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        text = ''.join(parts).strip()
        if text:
            return (f'*{text}*', 0)
        return ('', 0)
    
    # 处理 u 标签
    if tag_name == 'u':
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        text = ''.join(parts).strip()
        if text:
            return (f'<u>{text}</u>', 0)
        return ('', 0)
    
    # 处理 span 标签
    if tag_name == 'span':
        style = element.get('style', '')
        class_list = element.get('class', [])
        
        # 检查是否为大标题
        heading_level = 0
        if 'bbc_size' in class_list or 'bbc_size' in str(class_list):
            if '18pt' in style:
                heading_level = 1
            elif '16pt' in style:
                heading_level = 2
            elif '15pt' in style:
                heading_level = 3
        
        # 获取 span 内的文本
        parts = []
        trailing = 0
        for child in element.children:
            text, t = element_to_markdown(child, 0)
            parts.append(text)
            trailing = max(trailing, t)
        text = ''.join(parts).strip()
        
        if heading_level > 0 and text:
            return (f'\n\n{"#" * heading_level} {text}\n\n', 2)
        
        # 检查 color 样式：如果是黑色或普通颜色 span，只返回文本
        return (text, trailing)
    
    # 处理 font 标签
    if tag_name == 'font':
        parts = []
        trailing = 0
        for child in element.children:
            text, t = element_to_markdown(child, 0)
            parts.append(text)
            trailing = max(trailing, t)
        text = ''.join(parts).strip()
        return (text, trailing)
    
    # 处理 div 标签
    if tag_name == 'div':
        # 检查是否为 box（带边框的盒子）
        div_id = element.get('id', '')
        div_style = element.get('style', '')
        is_box = (div_id == 'box' or 
                  ('border-width' in div_style and 'border-style:solid' in div_style))
        
        has_onclick = element.get('onclick') is not None
        
        parts = []
        trailing = 0
        for child in element.children:
            text, t = element_to_markdown(child, 0)
            parts.append(text)
            trailing = max(trailing, t)
        text = ''.join(parts).strip()
        
        if not text:
            return ('', trailing)
        
        if is_box:
            lines = text.split('\n')
            quoted_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped:
                    quoted_lines.append(f'> {stripped}')
                else:
                    quoted_lines.append('>')
            return (f'\n\n' + '\n'.join(quoted_lines) + '\n\n', 2)
        
        if has_onclick:
            return (f'\n\n{text}\n\n', 2)
        
        return (f'\n{text}\n', 2)
    
    # 处理 a 标签
    if tag_name == 'a':
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        text = ''.join(parts).strip()
        href = element.get('href', '')
        if href and text:
            return (f'[{text}]({href})', 0)
        return (text, 0)
    
    # 处理 img 标签
    if tag_name == 'img':
        src = element.get('src', '')
        alt = element.get('alt', '图片')
        if src:
            return (f'\n\n![{alt}]({src})\n\n', 2)
        return ('', 0)
    
    # 处理 table 标签
    if tag_name == 'table':
        return (convert_table_to_markdown(element), 2)
    
    # 处理 tr, td, th（在 table 中处理）
    if tag_name in ('tr', 'td', 'th', 'thead', 'tbody', 'tfoot', 'colgroup', 'col'):
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        return (''.join(parts), 0)
    
    # 处理 ul/ol 标签
    if tag_name in ('ul', 'ol'):
        items = []
        for li in element.find_all('li', recursive=False):
            li_parts = []
            for child in li.children:
                text, _ = element_to_markdown(child, 0)
                li_parts.append(text)
            li_text = ''.join(li_parts).strip()
            if li_text:
                items.append(li_text)
        
        if not items:
            return ('', 0)
        
        result = '\n'
        for i, item in enumerate(items):
            if tag_name == 'ol':
                result += f'{i+1}. {item}\n'
            else:
                result += f'- {item}\n'
        return (result + '\n', 2)
    
    # 处理 li 标签（单独出现的情况）
    if tag_name == 'li':
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        return (''.join(parts).strip(), 0)
    
    # 处理 pre/code 标签
    if tag_name in ('pre', 'code'):
        parts = []
        for child in element.children:
            text, _ = element_to_markdown(child, 0)
            parts.append(text)
        text = ''.join(parts)
        return (f'\n\n```\n{text}\n```\n\n', 2)
    
    # 处理其他标签：递归处理子元素
    parts = []
    trailing = 0
    for child in element.children:
        text, t = element_to_markdown(child, 0)
        parts.append(text)
        trailing = max(trailing, t)
    return (''.join(parts), trailing)


def convert_table_to_markdown(table: Tag) -> str:
    """将 HTML 表格转换为 Markdown 表格"""
    rows = table.find_all('tr')
    if not rows:
        return ''
    
    markdown_rows = []
    for row in rows:
        cells = row.find_all(['td', 'th'])
        cell_texts = []
        for cell in cells:
            text = cell.get_text(strip=True)
            text = text.replace('|', '\\|')
            cell_texts.append(text)
        if cell_texts:
            markdown_rows.append(cell_texts)
    
    if not markdown_rows:
        return ''
    
    max_cols = max(len(row) for row in markdown_rows)
    for row in markdown_rows:
        while len(row) < max_cols:
            row.append('')
    
    result = '\n\n'
    result += '| ' + ' | '.join(markdown_rows[0]) + ' |\n'
    result += '| ' + ' | '.join(['---'] * max_cols) + ' |\n'
    for row in markdown_rows[1:]:
        result += '| ' + ' | '.join(row) + ' |\n'
    
    return result + '\n'


def convert_html_to_markdown(html_content: str, file_name: str = "") -> str:
    """将 HTML 内容转换为 Markdown"""
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 展开隐藏的 div
    soup = expand_hidden_divs(soup)
    
    # 获取 body 内容，如果没有 body 则使用整个 soup
    body = soup.find('body')
    if not body:
        body = soup
    
    # 处理 body 中的 HTML 注释 —— 直接移除
    for comment in body.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # 提取标题——在移除注释之后
    title = extract_title(soup)
    
    # 处理 body 的直接子元素
    parts = []
    for child in body.children:
        if isinstance(child, Comment):
            continue
        text, _ = element_to_markdown(child, 0)
        parts.append(text)
    
    result = ''.join(parts)
    
    # 清理文本
    result = clean_markdown(result)
    
    # 处理标题：如果 body 内容中已有 "# 标题" 格式则保留，否则用 title 添加
    if title:
        result_stripped = result.lstrip('\n')
        heading_line = f'# {title}'
        # 检查是否已以 markdown 标题开头
        if not result_stripped.startswith(heading_line):
            # 可能以纯文本标题开头，替换为 markdown 标题
            if result_stripped.startswith(title):
                result = heading_line + '\n\n' + result_stripped[len(title):].lstrip('\n')
            else:
                result = heading_line + '\n\n' + result
    
    # 最终清理
    result = clean_markdown(result)
    result = result.strip() + '\n'
    
    return result


def clean_markdown(text: str) -> str:
    """清理 Markdown 文本"""
    # 移除开头多余的空行
    text = text.lstrip('\n')
    # 多个连续空行 → 最多两个
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 移除行尾空白
    text = '\n'.join(line.rstrip() for line in text.split('\n'))
    # 修复：br 转成的 \n 后如果紧跟文本没有空行，适当处理
    # 修复空白的引用块行（> 后面没有内容）
    text = re.sub(r'^> $', '>', text, flags=re.MULTILINE)
    # 修复连续空引用行
    text = re.sub(r'(>\n){2,}', '>\n', text)
    return text


def process_directory(source_dir: Path, output_dir: Path):
    """递归处理目录，将所有 HTML 文件转换为 Markdown"""
    stats = {'processed': 0, 'skipped': 0, 'errors': 0}
    
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        
        rel_path = root_path.relative_to(source_dir)
        target_dir = output_dir / rel_path
        
        # 跳过 images/image 目录
        if root_path.name.lower() in ('images', 'image'):
            continue
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for file_name in files:
            if not file_name.lower().endswith(('.html', '.htm')):
                continue
            
            source_file = root_path / file_name
            md_name = Path(file_name).stem + '.md'
            target_file = target_dir / md_name
            
            try:
                with open(source_file, 'r', encoding='utf-8', errors='replace') as f:
                    html_content = f.read()
                
                md_content = convert_html_to_markdown(html_content, file_name)
                
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                stats['processed'] += 1
                if stats['processed'] % 100 == 0:
                    print(f"  已处理 {stats['processed']} 个文件...")
                
            except Exception as e:
                stats['errors'] += 1
                print(f"  [错误] {source_file}: {e}")
    
    return stats


def generate_index(output_dir: Path):
    """生成总索引文件"""
    index_content = """# 无限恐怖FX 规则库

本目录包含《无限恐怖FX》规则书的完整内容，从原始 HTML 文件自动提取并转换为 Markdown 格式。

## 目录结构

"""
    
    for item in sorted(output_dir.iterdir()):
        if item.is_dir() and item.name != '.git':
            md_count = sum(1 for _ in item.rglob('*.md'))
            index_content += f'- **{item.name}** ({md_count} 个文件)\n'
    
    index_content += f'\n> 自动生成于 {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    
    index_file = output_dir / 'README.md'
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    print(f"\n已生成索引文件: {index_file}")


def main():
    print("=" * 60)
    print("无限恐怖FX 规则提取工具")
    print("=" * 60)
    print()
    
    if not SOURCE_DIR.exists():
        print(f"[错误] 源目录不存在: {SOURCE_DIR}")
        sys.exit(1)
    
    print(f"源目录: {SOURCE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print()
    
    if OUTPUT_DIR.exists():
        import shutil
        shutil.rmtree(OUTPUT_DIR)
        print("已清空旧的输出目录")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("\n开始提取规则文件...")
    stats = process_directory(SOURCE_DIR, OUTPUT_DIR)
    
    print(f"\n处理完成!")
    print(f"  成功: {stats['processed']} 个文件")
    print(f"  跳过: {stats['skipped']} 个文件")
    print(f"  错误: {stats['errors']} 个文件")
    
    generate_index(OUTPUT_DIR)
    
    print("\n完成!")


if __name__ == '__main__':
    main()
