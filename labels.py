import requests
import argparse
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate labels for Magic: The Gathering card sets."
    )
    parser.add_argument(
        "input",
        help="A set code (e.g., ABC) or a path to a .txt file containing set codes.",
    )
    parser.add_argument(
        "--symbol",
        "-s",
        help="Path to a custom symbol image file to use instead of fetching from the web.",
    )
    return parser.parse_args()


def fetch_set_info(set_code):
    url = f"https://api.scryfall.com/sets/{set_code}"
    response = requests.get(url)
    if response.status_code == 200:
        set_data = response.json()
        return {
            "code": set_code,
            "name": set_data.get("name"),
            "date": set_data.get("released_at"),
        }
    elif response.status_code == 404:
        print(f"Error: Set '{set_code}' not found")
        exit(1)
    else:
        print(f"Error fetching set info: {response.status_code}")
        exit(1)
    return None


def is_text_file(filename):
    return filename.lower().endswith(".txt")


def process_text_file(filename, custom_symbol_path=None):
    try:
        # First count total lines to process
        with open(filename, "r") as file:
            total_lines = sum(1 for line in file if line.strip())

        # Process the file with progress tracking
        with open(filename, "r") as file:
            processed = 0
            for line in file:
                set_code = line.strip()
                if set_code:
                    processed += 1
                    print(f"Processing {processed}/{total_lines}: {set_code}", end="\r")
                    create_label(set_code, custom_symbol_path)

            # Print newline at the end to clear the progress line
            print(f"\nCompleted processing {processed} set codes from {filename}")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
    except Exception as e:
        print(f"Error reading file: {e}")


def add_set_symbol(image: Image, set_code, custom_symbol_path=None):
    symbol_image = None
    
    # Try to use custom symbol first if provided
    if custom_symbol_path and os.path.exists(custom_symbol_path):
        try:
            symbol_image = Image.open(custom_symbol_path)
            print(f"Using custom symbol from {custom_symbol_path}")
        except Exception as e:
            print(f"Error loading custom symbol: {e}")
            symbol_image = None
    
    # If no custom symbol or it failed to load, fetch from web
    if symbol_image is None:
        response = requests.get(
            url=f"https://mtgcollectionbuilder.com/images/symbols/sets/{set_code}.png"
        )
        if response.status_code == 200:
            png_image = response.content
            # Load the PNG image into Pillow
            symbol_image = Image.open(BytesIO(png_image))
        else:
            print(f"No symbol image for {set_code}")
            return

    # Get original dimensions
    img_width, img_height = symbol_image.size
    height = image.height

    # Calculate scaling factors for both height and width constraints
    height_scale = height / img_height
    width_scale = height / img_width  # Using height as max width

    # Use the smaller scaling factor to ensure both constraints are met
    scale = min(height_scale, width_scale)
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)

    # Resize symbol and convert to RGBA
    symbol_image = symbol_image.resize((new_width, new_height)).convert("RGBA")

    # Position symbol at the left side and vertically centered
    symbol_x = 0
    symbol_y = (height - new_height) // 2

    # Paste the symbol
    image.paste(symbol_image, (symbol_x, symbol_y), symbol_image)


def create_label(set_code, custom_symbol_path=None):
    set_code = set_code.upper()
    info = fetch_set_info(set_code)
    set_name = info["name"]
    release_date = info["date"]

    # Convert release_date from YYYY-MM-DD to MM/YYYY
    release_date = datetime.strptime(release_date, "%Y-%m-%d").strftime("%m/%Y")

    # Create a blank image with an RGB mode (white background)
    width = 760
    height = 140
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Define layout constants
    padding = 20  # Padding between elements

    # Load fonts
    original_font_size = 40
    font_big = ImageFont.load_default(original_font_size)
    font_small = ImageFont.load_default(30)

    # Get font metrics
    font_big_metrics = font_big.getmetrics()
    font_small_metrics = font_small.getmetrics()

    # Calculate ascent and descent for both fonts
    big_ascent, big_descent = font_big_metrics
    small_ascent, small_descent = font_small_metrics

    # Start position for text, will be the right side of the symbol
    text_start_x = height + padding

    # Calculate available width for text
    available_width = width - text_start_x - padding

    # Scale down font size if set name is too wide
    current_font_size = original_font_size
    font_big = ImageFont.load_default(current_font_size)
    text_width = font_big.getlength(set_name)

    while text_width > available_width and current_font_size > 20:  # Minimum size of 20
        current_font_size -= 1
        font_big = ImageFont.load_default(current_font_size)
        text_width = font_big.getlength(set_name)
        # Update metrics for new font size
        font_big_metrics = font_big.getmetrics()
        big_ascent, big_descent = font_big_metrics

    # Calculate text positions based on baseline
    middle_y = height / 2
    gap = 10  # Gap between the two text lines

    # Calculate y positions to center both lines around middle_y using baselines
    total_text_height = (
        (big_ascent + big_descent) + gap + (small_ascent + small_descent)
    )
    start_y = middle_y - total_text_height / 2

    # Position for set name (top line)
    set_name_y = start_y + big_ascent  # Align to baseline

    # Position for set code and date (bottom line)
    set_code_y = set_name_y + (big_ascent + big_descent)

    # Draw the texts
    draw.text(
        (text_start_x, set_name_y),
        set_name,
        font=font_big,
        fill=(0, 0, 0),
        anchor="ls",  # Left, baseline anchor
    )

    draw.text(
        (text_start_x, set_code_y),
        f"{set_code}   {release_date}",
        font=font_small,
        fill=(0, 0, 0),
        anchor="ls",  # Left, baseline anchor
    )

    add_set_symbol(image, set_code, custom_symbol_path)

    # Create the "labels" folder if it doesn't exist
    if not os.path.exists("./labels"):
        os.makedirs("./labels")

    # Save the image
    image.save(f"./labels/{set_code}_label.png")

    print(f"Label image created for {set_code}")

    return image


def main():
    args = parse_arguments()
    input_value = args.input
    custom_symbol_path = args.symbol

    # Check if the input is a file or a direct set code
    if "." in input_value:
        if is_text_file(input_value):
            process_text_file(input_value, custom_symbol_path)
        else:
            print(
                f"Error: '{input_value}' is not a text file. Please provide a .txt file or a set code."
            )
    else:
        # Treat as direct set code
        create_label(input_value, custom_symbol_path)


if __name__ == "__main__":
    main()
