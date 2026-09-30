import os

templates_dir = r"c:\Users\Ali Akintayo\Desktop\Marvelam\templates\email"
count = 0

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".html"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Fix inner padding touching edges
            new_content = content.replace(
                '<td style="padding:18px;">', '<td style="padding:18px !important;">'
            )

            # 2. Fix ITEMS ORDERED quantity
            new_content = new_content.replace(
                "ITEMS ORDERED ({{ orderitems|length|default:1 }})",
                "ITEMS ORDERED ({{ order.total_items|default:1 }})",
            )

            # In case it is spelled without spaces:
            new_content = new_content.replace(
                "ITEMS ORDERED({{ orderitems|length|default:1 }})",
                "ITEMS ORDERED ({{ order.total_items|default:1 }})",
            )

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
print(f"Fixed {count} files total")
