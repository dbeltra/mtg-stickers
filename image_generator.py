"""Image generation and processing for MTG set labels."""

import os
import logging
from datetime import datetime
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from mtg_api import fetch_set_symbol


def add_set_symbol(image: Image.Image, set_code: str, custom_symbol_path: Optional[str] = None, 
                  interactive: bool = True) -> str:
    """Add set symbol to the label image."""
    symbol_image = None
    
    # Try to use custom symbol first if provided
    if custom_symbol_path and os.path.exists(custom_symbol_path):
        try:
            symbol_image = Image.open(custom_symbol_path)
            logging.debug(f"Using custom symbol from {custom_symbol_path}")
        except Exception as e:
            logging.warning(f"Error loading custom symbol: {e}")
            symbol_image = None
    
    # If no custom symbol or it failed to load, fetch from web
    if symbol_image is None:
        symbol_image = fetch_set_symbol(set_code)
        if symbol_image is None:
            if interactive:
                return "NO_SYMBOL_FOUND"
            else:
                logging.debug(f"No symbol found for {set_code}, continuing without symbol")
                return "NO_SYMBOL_USED"

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
    return "SYMBOL_ADDED"


def create_label_image(set_code: str, set_name: str, release_date: str, 
                      custom_symbol_path: Optional[str] = None, 
                      interactive: bool = True) -> tuple[Image.Image, str]:
    """Create the actual label image with text and symbol."""
    # Convert release_date from YYYY-MM-DD to MM/YYYY
    try:
        formatted_date = datetime.strptime(release_date, "%Y-%m-%d").strftime("%m/%Y")
    except ValueError as e:
        logging.error(f"Invalid date format for {set_code}: {e}")
        raise

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
        f"{set_code}   {formatted_date}",
        font=font_small,
        fill=(0, 0, 0),
        anchor="ls",  # Left, baseline anchor
    )

    # Add set symbol and track result
    symbol_result = add_set_symbol(image, set_code, custom_symbol_path, interactive)
    
    return image, symbol_result
