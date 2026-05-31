#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作系统总复习PDF生成脚本
读取总复习内容整理.txt文件并生成详细的PDF文档
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import re

# 注册中文字体
try:
    pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/STHeiti Light.ttc'))
    pdfmetrics.registerFont(TTFont('SimHei', '/System/Library/Fonts/STHeiti Medium.ttc'))
    FONT_NAME = 'SimHei'
    FONT_NAME_BOLD = 'SimHei'
except:
    # 如果系统字体不可用，使用Helvetica
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

def parse_markdown_to_pdf(content_file, output_file):
    """
    解析Markdown格式的文本文件并生成PDF

    参数:
        content_file: 输入的文本文件路径
        output_file: 输出的PDF文件路径
    """

    # 读取文本内容
    with open(content_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # 定义样式
    styles = getSampleStyleSheet()

    # 标题样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30,
    )

    # 一级标题（章）
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontName=FONT_NAME_BOLD,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#000080',
    )

    # 二级标题（节）
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName=FONT_NAME_BOLD,
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15,
        textColor='#000080',
    )

    # 三级标题（小节）
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontName=FONT_NAME_BOLD,
        fontSize=12,
        spaceAfter=8,
        spaceBefore=12,
    )

    # 四级标题
    h4_style = ParagraphStyle(
        'CustomH4',
        parent=styles['Heading3'],
        fontName=FONT_NAME_BOLD,
        fontSize=11,
        spaceAfter=6,
        spaceBefore=10,
    )

    # 正文样式
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=15,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )

    # 代码块样式
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        leftIndent=20,
        spaceAfter=10,
        spaceBefore=10,
    )

    # 列表样式
    list_style = ParagraphStyle(
        'CustomList',
        parent=styles['BodyText'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=4,
    )

    # 构建文档内容
    story = []

    # 封面
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("操作系统总复习", title_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Operating System Review", body_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("详细版", body_style))
    story.append(PageBreak())

    # 解析内容
    in_code_block = False
    code_lines = []

    for line in lines:
        line = line.rstrip()

        # 跳过空行（但保留一定间距）
        if not line.strip():
            if not in_code_block:
                story.append(Spacer(1, 0.2*cm))
            continue

        # 检测代码块
        if line.strip().startswith('```'):
            if in_code_block:
                # 结束代码块
                if code_lines:
                    code_text = '\n'.join(code_lines)
                    story.append(Preformatted(code_text, code_style))
                code_lines = []
                in_code_block = False
            else:
                # 开始代码块
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # 检测标题
        if line.startswith('# '):
            # 一级标题
            text = line[2:].strip()
            story.append(Paragraph(text, h1_style))
        elif line.startswith('## '):
            # 二级标题
            text = line[3:].strip()
            story.append(Paragraph(text, h2_style))
        elif line.startswith('### '):
            # 三级标题
            text = line[4:].strip()
            story.append(Paragraph(text, h3_style))
        elif line.startswith('#### '):
            # 四级标题
            text = line[5:].strip()
            story.append(Paragraph(text, h4_style))
        elif line.startswith('---'):
            # 分隔线，添加分页
            story.append(PageBreak())
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            # 列表项
            text = line.strip()[2:]
            # 处理加粗
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph('• ' + text, list_style))
        elif line.strip().startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
            # 数字列表
            text = re.sub(r'^\d+\.\s+', '', line.strip())
            # 处理加粗
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            story.append(Paragraph(text, list_style))
        else:
            # 普通段落
            text = line.strip()
            # 处理加粗标记
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            # 处理行内代码
            text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)

            # 如果是表格行，跳过（简单处理）
            if '|' in text and text.count('|') >= 2:
                continue

            story.append(Paragraph(text, body_style))

    # 生成PDF
    try:
        doc.build(story)
        print(f"✓ PDF生成成功：{output_file}")

        # 检查文件大小
        file_size = os.path.getsize(output_file)
        file_size_kb = file_size / 1024
        file_size_mb = file_size / (1024 * 1024)

        if file_size_mb < 32:
            print(f"✓ 文件大小：{file_size_kb:.2f} KB ({file_size_mb:.2f} MB)")
            print(f"✓ 符合32MB限制要求")
        else:
            print(f"✗ 警告：文件大小 {file_size_mb:.2f} MB 超过32MB限制！")

        return True
    except Exception as e:
        print(f"✗ PDF生成失败：{e}")
        return False

def main():
    """主函数"""
    content_file = "/Users/fsr/Desktop/操作系统/总复习内容整理.txt"
    output_file = "/Users/fsr/Desktop/操作系统/操作系统总复习_详细版.pdf"

    print("=" * 60)
    print("操作系统总复习PDF生成工具")
    print("=" * 60)
    print(f"输入文件：{content_file}")
    print(f"输出文件：{output_file}")
    print("-" * 60)

    if not os.path.exists(content_file):
        print(f"✗ 错误：找不到输入文件 {content_file}")
        return

    print("正在生成PDF...")
    success = parse_markdown_to_pdf(content_file, output_file)

    if success:
        print("-" * 60)
        print("✓ 任务完成！")
    else:
        print("-" * 60)
        print("✗ 任务失败！")

if __name__ == "__main__":
    main()
