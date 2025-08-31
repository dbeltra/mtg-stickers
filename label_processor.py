"""Core label processing logic."""

import os
import logging
import time
import concurrent.futures
from typing import Optional, Dict, List

from mtg_api import fetch_set_info
from image_generator import create_label_image
from cli import print_progress_bar, format_duration


def create_label(set_code: str, custom_symbol_path: Optional[str] = None, 
                skip_existing: bool = False, dry_run: bool = False, 
                output_dir: str = "./labels", interactive: bool = True) -> str:
    """Create a label for a Magic: The Gathering set."""
    set_code = set_code.upper()
    output_path = f"{output_dir}/{set_code}_label.png"
    
    # Check if file already exists and should be skipped
    if skip_existing and os.path.exists(output_path):
        logging.debug(f"Skipping {set_code} - label already exists")
        return "skipped"
    
    # Fetch set information
    info = fetch_set_info(set_code)
    if not info:
        logging.error(f"Failed to fetch information for {set_code}")
        return "failed"
    
    set_name = info["name"]
    release_date = info["date"]
    
    if not set_name or not release_date:
        logging.error(f"Incomplete set information for {set_code}")
        return "failed"

    if dry_run:
        # Convert date for display
        try:
            from datetime import datetime
            formatted_date = datetime.strptime(release_date, "%Y-%m-%d").strftime("%m/%Y")
            logging.info(f"Would create: {set_code}_label.png - {set_name} ({formatted_date})")
            return "success"
        except ValueError:
            logging.info(f"Would create: {set_code}_label.png - {set_name}")
            return "success"

    # Create the label image
    try:
        image, symbol_result = create_label_image(set_code, set_name, release_date, 
                                                 custom_symbol_path, interactive)
        
        # Handle symbol not found in interactive mode
        if symbol_result == "NO_SYMBOL_FOUND" and interactive:
            from cli import prompt_for_symbol
            user_choice = prompt_for_symbol(set_code, set_name)
            
            if user_choice == "SKIP":
                logging.info(f"Skipped {set_code} - user chose to skip")
                return "skipped"
            elif user_choice == "NO_SYMBOL":
                # Recreate image without symbol
                image, _ = create_label_image(set_code, set_name, release_date, 
                                           None, False)
                logging.info(f"Created text-only label for {set_code}")
            elif user_choice and user_choice not in ["SKIP", "NO_SYMBOL"]:
                # User provided custom symbol path
                image, _ = create_label_image(set_code, set_name, release_date, 
                                           user_choice, False)
                logging.info(f"Created label for {set_code} with custom symbol")
        elif symbol_result == "NO_SYMBOL_FOUND" and not interactive:
            logging.warning(f"No symbol found for {set_code}, creating text-only label")
            
    except Exception as e:
        logging.error(f"Failed to create image for {set_code}: {e}")
        return "failed"

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the image
    try:
        image.save(output_path)
        logging.info(f"Created label: {set_code}_label.png - {set_name}")
        return "success"
    except Exception as e:
        logging.error(f"Failed to save label for {set_code}: {e}")
        return "failed"


def process_text_file(filename: str, custom_symbol_path: Optional[str] = None, 
                     skip_existing: bool = False, dry_run: bool = False,
                     output_dir: str = "./labels", parallel: Optional[int] = None) -> Dict[str, int]:
    """Process a text file containing set codes with progress tracking and error handling."""
    stats = {"processed": 0, "skipped": 0, "failed": 0, "total": 0}
    
    try:
        # First count total lines to process
        with open(filename, "r") as file:
            set_codes = [line.strip().upper() for line in file if line.strip()]
            stats["total"] = len(set_codes)

        if stats["total"] == 0:
            logging.warning(f"No set codes found in {filename}")
            return stats

        logging.info(f"Processing {stats['total']} set codes from {filename}")
        
        if dry_run:
            logging.info("DRY RUN - No files will be created")

        # Process sets (parallel or sequential)
        start_time = time.time()
        
        if parallel and parallel > 1:
            stats = _process_parallel(set_codes, custom_symbol_path, skip_existing, 
                                    dry_run, output_dir, parallel, stats)
        else:
            # For batch processing, ask user about interactive mode for missing symbols
            interactive_batch = len(set_codes) <= 5  # Only interactive for small batches
            if len(set_codes) > 5 and not dry_run:
                from cli import confirm_action
                interactive_batch = confirm_action(
                    f"Enable interactive prompts for missing symbols? "
                    f"({len(set_codes)} sets to process)", 
                    default=False
                )
            
            stats = _process_sequential(set_codes, custom_symbol_path, skip_existing, 
                                      dry_run, output_dir, stats, interactive_batch)
        
        # Show final summary with timing
        elapsed = time.time() - start_time
        if not logging.getLogger().isEnabledFor(logging.DEBUG):
            print()  # Clear progress line
            
        logging.info(f"Completed in {format_duration(elapsed)}: {stats['processed']} processed, {stats['skipped']} skipped, {stats['failed']} failed")

    except FileNotFoundError:
        logging.error(f"File '{filename}' not found")
        stats["failed"] = 1
    except Exception as e:
        logging.error(f"Error reading file {filename}: {e}")
        stats["failed"] = 1
        
    return stats


def _process_sequential(set_codes: List[str], custom_symbol_path: Optional[str], 
                       skip_existing: bool, dry_run: bool, output_dir: str, 
                       stats: Dict[str, int], interactive_batch: bool = False) -> Dict[str, int]:
    """Process set codes sequentially with progress bar."""
    for i, set_code in enumerate(set_codes, 1):
        # Progress bar
        if not logging.getLogger().isEnabledFor(logging.DEBUG):
            print_progress_bar(i-1, stats['total'], prefix="Progress", 
                             suffix=f"Processing {set_code}")
        
        try:
            result = create_label(set_code, custom_symbol_path, skip_existing, 
                                dry_run, output_dir, interactive_batch)
            if result == "skipped":
                stats["skipped"] += 1
            elif result == "failed":
                stats["failed"] += 1
            else:
                stats["processed"] += 1
                
        except Exception as e:
            logging.error(f"Unexpected error processing {set_code}: {e}")
            stats["failed"] += 1
    
    # Final progress bar
    if not logging.getLogger().isEnabledFor(logging.DEBUG):
        print_progress_bar(stats['total'], stats['total'], prefix="Progress", 
                         suffix="Complete!")
    
    return stats


def _process_parallel(set_codes: List[str], custom_symbol_path: Optional[str], 
                     skip_existing: bool, dry_run: bool, output_dir: str, 
                     parallel: int, stats: Dict[str, int]) -> Dict[str, int]:
    """Process set codes in parallel with progress tracking."""
    completed = 0
    
    def process_single(set_code: str) -> str:
        # Parallel processing is always non-interactive
        return create_label(set_code, custom_symbol_path, skip_existing, 
                          dry_run, output_dir, interactive=False)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        # Submit all tasks
        future_to_code = {executor.submit(process_single, code): code 
                         for code in set_codes}
        
        # Process completed tasks
        for future in concurrent.futures.as_completed(future_to_code):
            set_code = future_to_code[future]
            completed += 1
            
            # Update progress bar
            if not logging.getLogger().isEnabledFor(logging.DEBUG):
                print_progress_bar(completed, stats['total'], prefix="Progress", 
                                 suffix=f"({parallel} parallel)")
            
            try:
                result = future.result()
                if result == "skipped":
                    stats["skipped"] += 1
                elif result == "failed":
                    stats["failed"] += 1
                else:
                    stats["processed"] += 1
            except Exception as e:
                logging.error(f"Unexpected error processing {set_code}: {e}")
                stats["failed"] += 1
    
    return stats


def validate_set_codes(set_codes: List[str]) -> Dict[str, List[str]]:
    """Validate a list of set codes without generating labels."""
    results = {"valid": [], "invalid": [], "errors": []}
    
    logging.info(f"Validating {len(set_codes)} set codes...")
    
    for i, set_code in enumerate(set_codes, 1):
        if not logging.getLogger().isEnabledFor(logging.DEBUG):
            print_progress_bar(i-1, len(set_codes), prefix="Validating", 
                             suffix=f"Checking {set_code}")
        
        try:
            info = fetch_set_info(set_code)
            if info and info.get("name"):
                results["valid"].append(f"{set_code}: {info['name']}")
            else:
                results["invalid"].append(set_code)
        except Exception as e:
            results["errors"].append(f"{set_code}: {str(e)}")
    
    # Final progress
    if not logging.getLogger().isEnabledFor(logging.DEBUG):
        print_progress_bar(len(set_codes), len(set_codes), prefix="Validating", 
                         suffix="Complete!")
        print()
    
    return results
