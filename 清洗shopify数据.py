import pandas as pd
import re
from bs4 import BeautifulSoup
import sys
import os


def clean_html_content(html_content):
    """
    清理HTML内容，移除指定的标签和内容
    """
    if pd.isna(html_content) or html_content == '':
        return html_content
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(str(html_content), 'html.parser')
    # 移除所有a标签及其内容
    for tag in soup.find_all('a'):
        tag.decompose()
    # 移除所有video标签及其内容
    for tag in soup.find_all('video'):
        tag.decompose()
    # 移除所有img标签及其内容
    for tag in soup.find_all('img'):
        tag.decompose()
    for tag in soup.find_all('button'):
        tag.decompose()
    for tag in soup.find_all('svg'):
        tag.decompose()
    # 返回清理后的HTML内容
    return str(soup)


def remove_content_after_characters(content, remove_chars):
    """
    删除指定字符及其后面的所有内容
    Args:
        content (str): 原始内容
        remove_chars (list): 要删除的字符列表
    """
    if pd.isna(content) or content == '' or not remove_chars:
        return content

    result = str(content)

    # 找到最早出现的字符位置
    min_index = len(result)
    found_char = None

    for char in remove_chars:
        index = result.find(char)
        if index != -1 and index < min_index:
            min_index = index
            found_char = char

    # 如果找到了任何字符，就截取到该位置
    if found_char is not None:
        result = result[:min_index]

    return result


def remove_content_between_strings(content, remove_ranges):
    """
    删除指定字符串区间内的所有内容（包括起始和结束字符串）
    Args:
        content (str): 原始内容
        remove_ranges (list): 要删除的区间列表，每个元素为 [起始字符串, 结束字符串]
    """
    if pd.isna(content) or content == '' or not remove_ranges:
        return content

    result = str(content)

    # 对每个删除区间进行处理
    for start_str, end_str in remove_ranges:
        if not start_str or not end_str:
            continue

        # 使用循环来处理多个匹配的区间
        while True:
            start_index = result.find(start_str)
            if start_index == -1:
                break  # 没有找到起始字符串，跳出循环

            # 从起始字符串之后开始寻找结束字符串
            end_search_start = start_index + len(start_str)
            end_index = result.find(end_str, end_search_start)

            if end_index == -1:
                # 没有找到结束字符串，删除从起始字符串到文本末尾的所有内容
                result = result[:start_index]
                break
            else:
                # 找到了结束字符串，删除整个区间（包括起始和结束字符串）
                end_index += len(end_str)
                result = result[:start_index] + result[end_index:]

    return result


def replace_text_content(content, text_replacements, remove_chars=None, remove_ranges=None):
    """
    替换指定的文本内容、删除指定字符后的内容、删除指定区间内容 - 仅针对Body (HTML)列
    Args:
        content: 原始内容
        text_replacements (dict): 要替换的文本字典
        remove_chars (list): 要删除的字符列表
        remove_ranges (list): 要删除的区间列表，每个元素为 [起始字符串, 结束字符串]
    """
    if pd.isna(content) or content == '':
        return content

    result = str(content)

    # 先进行文本替换
    if text_replacements:
        for old_text, new_text in text_replacements.items():
            result = result.replace(old_text, new_text)

    # 然后删除指定区间内容
    if remove_ranges:
        result = remove_content_between_strings(result, remove_ranges)

    # 最后删除指定字符及其后面的内容
    if remove_chars:
        result = remove_content_after_characters(result, remove_chars)

    return result


def process_csv_file(csv_file_path, text_replacements=None, remove_chars=None, remove_ranges=None):
    """
    处理CSV文件 - 只处理Body (HTML)列，其他列保持不变
    Args:
        csv_file_path (str): CSV文件路径
        text_replacements (dict): 要替换的文本字典，格式为 {原文本: 新文本}
        remove_chars (list): 要删除的字符列表，删除字符及其后面的所有内容
        remove_ranges (list): 要删除的区间列表，每个元素为 [起始字符串, 结束字符串]
    """
    try:
        # 读取CSV文件
        print(f"正在读取CSV文件: {csv_file_path}")
        df = pd.read_csv(csv_file_path, encoding='utf-8')

        # 检查是否存在"Body (HTML)"列
        if "Body (HTML)" not in df.columns:
            print("错误: CSV文件中未找到'Body (HTML)'列")
            print(f"可用的列: {', '.join(df.columns.tolist())}")
            return False

        print(f"找到 {len(df)} 行数据")
        print(f"只处理 'Body (HTML)' 列，其他 {len(df.columns) - 1} 列保持不变")

        # 备份原始的Body (HTML)列数据
        original_body_html = df["Body (HTML)"].copy()

        # 处理每一行的"Body (HTML)"列 - 清理HTML标签
        print("正在清理HTML标签...")
        df["Body (HTML)"] = df["Body (HTML)"].apply(clean_html_content)

        # 进行文本替换、区间删除和字符删除
        if text_replacements or remove_ranges or remove_chars:
            print("正在进行文本替换、区间删除和字符删除...")
            df["Body (HTML)"] = df["Body (HTML)"].apply(
                lambda x: replace_text_content(x, text_replacements, remove_chars, remove_ranges)
            )

        # 统计处理结果
        changed_rows = sum(original_body_html != df["Body (HTML)"])
        print(f"共处理了 {changed_rows} 行数据")

        # 保存回原文件
        print(f"正在保存到原文件: {csv_file_path}")
        df.to_csv(csv_file_path, index=False, encoding='utf-8')
        print("处理完成！")
        return True

    except FileNotFoundError:
        print(f"错误: 找不到文件 {csv_file_path}")
        return False
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        return False


if __name__ == "__main__":
    # 文本替换配置 - 在这里设置要替换的文本
    TEXT_REPLACEMENTS = {
        "bando": "starlinkprox",
        "Soundandcircle": "Starlinkprox",
        # 添加更多需要替换的文本...
        # "要替换的文本": "替换后的文本",
    }
    # 区间删除配置 - 在这里设置要删除的字符串区间
    REMOVE_RANGES = [
        # ["$", "0"],  # 删除特定div标签及其内容
        ["<!-- 开始注释", "结束注释 -->"],  # 删除注释区间
        ["<script", "</script>"],  # 删除所有script标签
        # 添加更多需要删除的区间...
        # ["起始字符串", "结束字符串"],
    ]
    # 字符删除配置 - 在这里设置要删除的字符
    REMOVE_CHARS = [
        # '<ul>',  # 删除<ul>及后面的所有内容
        # 添加更多需要删除的字符...
    ]
    print("CSV HTML内容清理工具 - 仅处理Body (HTML)列")
    print("=" * 60)
    input_dir = '.'
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv') and not filename.endswith('.csv.backup'):
            csv_file_path = os.path.join(input_dir, filename)
            print(f"\n正在处理文件: {csv_file_path}")
            success = process_csv_file(csv_file_path, TEXT_REPLACEMENTS, REMOVE_CHARS, REMOVE_RANGES)
            if success:
                print(f"✅ {filename} 处理成功！")
            else:
                print(f"❌ {filename} 处理失败！")


# ==========================================
# 使用示例和测试
# ==========================================

def test_remove_functions():
    """
    测试字符删除和区间删除功能
    """

    # 测试字符删除功能
    print("=== 字符删除功能测试 ===")
    char_test_cases = [
        ("这是正常文本#删除这部分", ['#'], "这是正常文本"),
        ("保留这部分@删除这部分", ['@'], "保留这部分"),
        ("多个字符#测试@删除", ['#', '@'], "多个字符"),
        ("HTML内容<!--注释内容-->", ['<!--'], "HTML内容"),
        ("正常文本没有特殊字符", ['#', '@'], "正常文本没有特殊字符"),
        ("", ['#'], ""),
        (None, ['#'], None),
    ]

    for i, (input_text, chars, expected) in enumerate(char_test_cases, 1):
        result = remove_content_after_characters(input_text, chars)
        status = "✅" if result == expected else "❌"
        print(f"测试 {i}: {status}")
        print(f"  输入: {input_text}")
        print(f"  字符: {chars}")
        print(f"  期望: {expected}")
        print(f"  结果: {result}")
        print("-" * 30)

    # 测试区间删除功能
    print("\n=== 区间删除功能测试 ===")
    range_test_cases = [
        ("保留<start>删除这部分<end>保留", [["<start>", "<end>"]], "保留保留"),
        ("前面内容<!-- 注释内容 -->后面内容", [["<!--", "-->"]], "前面内容后面内容"),
        ("多个<del>删除1</del>区间<del>删除2</del>测试", [["<del>", "</del>"]], "多个区间测试"),
        ("<script>删除脚本</script>正常内容<style>删除样式</style>",
         [["<script>", "</script>"], ["<style>", "</style>"]], "正常内容"),
        ("没有匹配的区间", [["<start>", "<end>"]], "没有匹配的区间"),
        ("只有开始<start>没有结束", [["<start>", "<end>"]], "只有开始"),
        ("", [["<start>", "<end>"]], ""),
        (None, [["<start>", "<end>"]], None),
    ]

    for i, (input_text, ranges, expected) in enumerate(range_test_cases, 1):
        result = remove_content_between_strings(input_text, ranges)
        status = "✅" if result == expected else "❌"
        print(f"测试 {i}: {status}")
        print(f"  输入: {input_text}")
        print(f"  区间: {ranges}")
        print(f"  期望: {expected}")
        print(f"  结果: {result}")
        print("-" * 30)

    # 测试综合功能
    print("\n=== 综合功能测试 ===")
    combined_test_cases = [
        (
            "替换test为TEST，删除<del>这部分</del>，删除#后面内容",
            {"test": "TEST"},
            ["#"],
            [["<del>", "</del>"]],
            "替换TEST为TEST，删除，删除"
        ),
    ]

    for i, (input_text, replacements, chars, ranges, expected) in enumerate(combined_test_cases, 1):
        result = replace_text_content(input_text, replacements, chars, ranges)
        status = "✅" if result == expected else "❌"
        print(f"综合测试 {i}: {status}")
        print(f"  输入: {input_text}")
        print(f"  替换: {replacements}")
        print(f"  字符删除: {chars}")
        print(f"  区间删除: {ranges}")
        print(f"  期望: {expected}")
        print(f"  结果: {result}")
        print("-" * 30)

# 如果需要测试，取消下面的注释
# test_remove_functions()
