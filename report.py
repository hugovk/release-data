import frontmatter
import sys
import time
from glob import glob

products = {}
count = 0
count_auto = 0
products_dir = sys.argv[1] if len(sys.argv) > 1 else 'website/products/'
for product_file in sorted(list(glob(f'{products_dir}/*.md'))):
    with open(product_file) as f:
        data = frontmatter.load(f)
        count += 1
        title = data['title']
        permalink = data['permalink']
        if 'auto' in data:
            count_auto += 1
            method = list(data['auto'][0].keys())[0]
            products[title] = [permalink, '✔️', method]
        else:
            products[title] = [permalink, '❌', 'n/a']


print(f"As of {time.strftime('%Y-%m-%d')}, {count_auto} of the {count} products"
      f" tracked by endoflife.date have automatically tracked releases:")
print()
print('| Product | Permalink | Auto | Method |')
print('|---------|-----------|------|--------|')
for product in sorted(products.keys(), key=str.lower):
    permalink, auto, method = products[product]
    print(f"| {product} | [`{permalink}`](https://endoflife.date{permalink}) | {auto} | {method} |")
print()
print('This table has been generated by [report.py](/report.py).')
