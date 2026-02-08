import requests
from PIL import Image, ImageDraw, ImageFont

# Load logo file
logo = Image.open("src/assets/canyon-logo.png")

# Create a new RGBA image (work in full color with alpha)
image = Image.new("RGBA", (296, 128), (255, 255, 255, 255))  # white background

# Convert and prepare logo
logo.thumbnail((image.height, image.height), resample=Image.NEAREST)
logo = logo.rotate(-90, expand=True)
if logo.mode != "RGBA":
    logo = logo.convert("RGBA")

# Composite logo onto canvas
image.alpha_composite(logo, (0, 0))

# Initialize the drawing context
draw = ImageDraw.Draw(image)
draw.fontmode = "1"  # disable anti-aliasing


FONT_SIZE = 32


font_regular = ImageFont.truetype(
    "src/assets/dinish-otf/DINish-Medium.otf", size=FONT_SIZE
)
font_bold = ImageFont.truetype("src/assets/dinish-otf/DINish-Bold.otf", size=FONT_SIZE)


X_OFFSET = 28

BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 255)

start_y = -5
padding_y = 2
text_positions = [
    (X_OFFSET, y) for y in range(start_y, image.height - padding_y, FONT_SIZE)
]


# Define the text lines
gear_name = "Aeroad CF SLX 8"
gear_distance = "27.023 km"
gear_weekly_distance = "127 km (7d)"

# Write the text on the image
draw.text(text_positions[0], gear_name, fill=BLACK, font=font_bold)
draw.text(text_positions[1], gear_distance, fill=BLACK, font=font_regular)
draw.text(text_positions[3], gear_weekly_distance, fill=BLACK, font=font_regular)


# Define the color palette (white, black, red)
palette = [
    255,
    255,
    255,  # white
    0,
    0,
    0,  # black
    255,
    0,
    0,  # red
]

# Create a palette image for quantization
palette_img = Image.new("P", (1, 1))
palette_img.putpalette(palette)

# Convert to paletted format at the end
paletted_image = image.convert("RGB").quantize(palette=palette_img)

paletted_image.show()
