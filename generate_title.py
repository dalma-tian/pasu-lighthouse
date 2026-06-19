"""Generate title typography image for pasu-lighthouse"""
from PIL import Image, ImageDraw, ImageFont
import os

output_path = os.path.join(os.path.dirname(__file__), "static", "title-typography.png")

# Canvas: wide banner 4:1 ratio
width, height = 1200, 300

# Create transparent image
img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Font paths
serif_font_path = "/c/Windows/Fonts/HANBatang.ttf"
sans_font_path = "/c/Windows/Fonts/NotoSansKR-VF.ttf"

# Main title
main_text = "파수의 등대"
main_font_size = 80
main_font = ImageFont.truetype(serif_font_path, main_font_size)

# Subtitle
sub_text = "금융정보의 빛이 되는 곳"
sub_font_size = 28
sub_font = ImageFont.truetype(sans_font_path, sub_font_size)

# Color: deep charcoal #1a1a2e
color_main = (26, 26, 46, 255)
color_sub = (26, 26, 46, 160)  # ~62% opacity

# Calculate text positions (centered)
main_bbox = draw.textbbox((0, 0), main_text, font=main_font)
main_w = main_bbox[2] - main_bbox[0]
main_h = main_bbox[3] - main_bbox[1]

sub_bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
sub_w = sub_bbox[2] - sub_bbox[0]
sub_h = sub_bbox[3] - sub_bbox[1]

# Center vertically with main text slightly above center
gap = 15
total_h = main_h + sub_h + gap
start_y = (height - total_h) // 2

# Draw main text
main_x = (width - main_w) // 2
draw.text((main_x, start_y), main_text, font=main_font, fill=color_main)

# Draw subtitle
sub_x = (width - sub_w) // 2
sub_y = start_y + main_h + gap
draw.text((sub_x, sub_y), sub_text, font=sub_font, fill=color_sub)

# Save as PNG
img.save(output_path, "PNG")
print(f"Saved: {output_path}")
print(f"Size: {os.path.getsize(output_path)} bytes, Dimensions: {img.size}")
