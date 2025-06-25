import csv
import json
import sys
import time
from collections import defaultdict
from slugify import slugify
import random
import string
import os
import datetime

if 'unicode' not in globals():
    unicode = str

def generate_beauty_sku():
    # 随机生成5位字母和数字组成的后缀
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    # 生成以beauty开头的SKU
    # 获取当前时间戳的最后两位
    timestamp_last_two = str(int(time.time()))[-2:]
    sku = "beauty" + suffix + timestamp_last_two
    return sku

def process_shopify_csv(input_csv, output_json):
    # 读取CSV数据并按Handle分组
    products = defaultdict(list)
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            handle = row['Handle']
            products[handle].append(row)

    # 处理每个产品组
    output_data = []
    valid_count = 0
    for handle, variants in products.items():
        if valid_count >= 50:
            break
        main_variant = variants[0]
        # 收集所有图片（主图 + 变体图）
        all_images = set()
        for variant in variants:
            if variant['Image Src']:
                all_images.add(variant['Image Src'])
        all_images = list(all_images)
        images = []
        position = 0
        for image in all_images:
            image_data = {
                "src": image,
                "position": position
            }
            position += 1
            images.append(image_data)
        # 只保留 position>=1 的后5张图片，并重新编号
        filtered_images = [img for img in images if img["position"] >= 1]
        filtered_images = filtered_images[-5:]
        for idx, img in enumerate(filtered_images):
            img["position"] = idx
        images = filtered_images
        # 跳过images中有任何src为空的产品
        if any(img["src"] == '' for img in images):
            continue
        # 初始化产品信息
        product = {
            "product": {
                "title": main_variant['Title'],
                "type": "variable",
                "description": main_variant['Body (HTML)'],
                "price": adjust_prices(main_variant['Variant Price']),
                "regular_price": adjust_prices(main_variant['Variant Price']),
                "status": "publish",
                "managing_stock":True,
                "in_stock": True,
                "stock_quantity": random.randint(1000, 5000),
                "categories": [tag.strip() for tag in main_variant['Tags'].split(',') if tag.strip()],
                "images": images,
                "attributes": [],
                "variations": []
            }
        }
        # 收集所有属性信息
        attribute_map = {}
        seen_attribute_names = set()  # 用于去重
        for option_num in range(1, 4):
            name_key = f'Option{option_num} Name'
            value_key = f'Option{option_num} Value'

            if name_key in main_variant and main_variant[name_key]:
                attr_name = main_variant[name_key].strip()
                if attr_name not in seen_attribute_names:
                    attr_slug = slugify(attr_name)
                    options = set()
                    for variant in variants:
                        if variant[value_key]:
                            options.add(variant[value_key].strip())
                    if options:
                        attribute_map[option_num] = {
                            "name": attr_name,
                            "slug": attr_slug,
                            "options": sorted(list(options))
                        }
                    seen_attribute_names.add(attr_name)
        for opt_num, attr_info in attribute_map.items():
            product['product']["attributes"].append({
                "name": attr_info["name"],
                "slug": attr_info["slug"],
                "options": attr_info["options"],
                "visible": True,
                "variation": True
            })
        search_variants = [item for item in variants if bool(item.get("Option1 Name", "").strip())]
        for variant in search_variants:
            variation = {
                "regular_price": adjust_prices(variant['Variant Price']),
                "price": adjust_prices(variant['Variant Price']),
                "sku": variant['Variant SKU'],
                "manage_stock": True,
                "stock_quantity": random.randint(1000, 5000),
                "in_stock": True,
                "attributes": [],
                "image": []
            }
            for opt_num in attribute_map.keys():
                value_key = f'Option{opt_num} Value'
                attr_info = attribute_map[opt_num]
                if variant[value_key]:
                    variation["attributes"].append({
                        "name": attr_info["name"],
                        "slug": attr_info["slug"],
                        "option": variant[value_key].strip()
                    })
            product['product']["variations"].append(variation)
        output_data.append(product)
        valid_count += 1
    # 保存为JSON文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"成功生成 {len(output_data)} 个产品的转换数据")

def adjust_prices(price):
    if not price:
        price = 99
    max_price = 200  # 设定最大价格为300元
    price = float(price)
    # 如果价格超过500，则进行折扣循环
    while price > max_price:
        price *= 0.9  # 按折扣因子递减
    if price < 10 and price > 5:
        price = 9.99
    elif price <= 5:
        price = 4.99
    else:
        price = price*0.95
    return float(f"{float(price):.2f}")


if __name__ == '__main__':
    # 自动遍历当前目录下所有csv文件（不包括.backup）
    input_dir = '.'
    output_dir = f'./product-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    os.makedirs(output_dir, exist_ok=True)
    for filename in os.listdir(input_dir):
        if filename.endswith('.csv') and not filename.endswith('.csv.backup'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename.replace('.csv', '.json'))
            print(f"正在处理: {input_file} -> {output_file}")
            try:
                process_shopify_csv(input_file, output_file)
            except Exception as e:
                print(f"处理 {filename} 时出错: {e}")
