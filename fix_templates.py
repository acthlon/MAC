import os
import re

templates_dir = r"c:\Users\Ali Akintayo\Desktop\Marvelam\templates\email"
count = 0

div_old = r"<div style=\"width:52px;height:52px;border:1px solid #2e2600;background-color:#141105;border-radius:3px;line-height:50px;text-align:center;\">\s*<span style=\"font-size:22px;\">.?<\/span>\s*<\/div>"
div_new = r"""<div style=\"width:52px;height:52px;border:1px solid #2e2600;background-color:#141105;border-radius:3px;overflow:hidden;text-align:center;\">
                        {% if orderitem.image %}
                          <img src=\"{{ website_url }}{{ orderitem.image.url }}\" alt=\"Item\" style=\"width:100%;height:100%;object-fit:cover;\" />
                        {% else %}
                          <span style=\"font-size:22px;line-height:50px;\">📦</span>
                        {% endif %}
                      </div>"""

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".html"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace image div
            new_content = re.sub(div_old, div_new, content)

            # Replace name
            new_content = new_content.replace(
                '{{ orderitem.content_object.name|default:"Custom Marvelam Garment / Material" }}',
                "{{ orderitem.catalog_name }}",
            )
            new_content = new_content.replace(
                '{{ orderitem.content_object.name|default:"Custom Marvelam Garment" }}',
                "{{ orderitem.catalog_name }}",
            )

            # Replace amounts with floatformat
            new_content = new_content.replace(
                "{{ orderitem.sub_total|default:order.total_amount }}",
                '{{ orderitem.sub_total|default:order.total_amount|floatformat:"2g" }}',
            )

            # Also fix totals at the bottom of the emails
            new_content = new_content.replace(
                "{{ order.sub_total_amount }}",
                '{{ order.sub_total_amount|floatformat:"2g" }}',
            )
            new_content = new_content.replace(
                "{{ order.shipping_fee }}", '{{ order.shipping_fee|floatformat:"2g" }}'
            )
            new_content = new_content.replace(
                "{{ order.total_discount }}",
                '{{ order.total_discount|floatformat:"2g" }}',
            )
            new_content = new_content.replace(
                "{{ order.total_amount }}", '{{ order.total_amount|floatformat:"2g" }}'
            )

            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                count += 1
print(f"Fixed {count} files total")
