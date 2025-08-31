#!/usr/bin/env python3
"""
MTG Label Generator - Main entry point

Generate professional-looking labels for Magic: The Gathering card sets.
"""

import logging
import sys

from cli import parse_arguments, setup_logging, is_text_file, confirm_action
from label_processor import create_label, process_text_file, validate_set_codes
from mtg_api import get_recent_sets


def show_recent_sets():
    """Display recent MTG sets with their codes."""
    print("Recent Magic: The Gathering Sets:")
    print("=" * 50)
    
    sets = get_recent_sets(25)
    if not sets:
        print("Unable to fetch recent sets. Please check your internet connection.")
        return
    
    for set_data in sets:
        code = set_data.get("code", "").upper()
        name = set_data.get("name", "Unknown")
        date = set_data.get("released_at", "Unknown")
        set_type = set_data.get("set_type", "").replace("_", " ").title()
        
        print(f"{code:6} | {name:35} | {date:10} | {set_type}")
    
    print("\nUse any of these codes with the tool, e.g.:")
    if sets:
        example_code = sets[0].get("code", "AFR").upper()
        print(f"  python labels.py {example_code}")


def main():
    """Main entry point for the MTG label generator."""
    args = parse_arguments()
    
    # Handle special commands that don't require input
    if args.list_recent:
        show_recent_sets()
        return 0
    
    # Validate that input is provided for other operations
    if not args.input:
        if args.validate:
            logging.error("--validate requires an input file or set code")
            return 1
        logging.error("Input is required. Use --help for usage information.")
        return 1
    
    # Setup logging based on verbosity flags
    setup_logging(args.verbose, args.quiet)
    
    # Validate conflicting arguments
    if args.skip and args.force:
        logging.error("Cannot use --skip and --force together")
        return 1
    
    input_value = args.input
    custom_symbol_path = args.symbol
    skip_existing = args.skip and not args.force
    dry_run = args.dry_run
    output_dir = args.output_dir
    parallel = args.parallel

    # Handle validation mode
    if args.validate:
        if "." in input_value and is_text_file(input_value):
            try:
                with open(input_value, "r") as file:
                    set_codes = [line.strip().upper() for line in file if line.strip()]
            except FileNotFoundError:
                logging.error(f"File '{input_value}' not found")
                return 1
        else:
            set_codes = [input_value.upper()]
        
        results = validate_set_codes(set_codes)
        
        print(f"\nValidation Results:")
        print(f"Valid sets: {len(results['valid'])}")
        print(f"Invalid sets: {len(results['invalid'])}")
        print(f"Errors: {len(results['errors'])}")
        
        if results['valid']:
            print(f"\n✓ Valid Sets:")
            for item in results['valid']:
                print(f"  {item}")
        
        if results['invalid']:
            print(f"\n✗ Invalid Sets:")
            for item in results['invalid']:
                print(f"  {item}")
        
        if results['errors']:
            print(f"\n⚠ Errors:")
            for item in results['errors']:
                print(f"  {item}")
        
        return 1 if results['invalid'] or results['errors'] else 0

    # Warn about parallel processing limitations
    if parallel and parallel > 1:
        if not confirm_action(f"Process {parallel} sets in parallel? This may hit API rate limits", default=True):
            logging.info("Operation cancelled by user")
            return 0

    # Check if the input is a file or a direct set code
    if "." in input_value:
        if is_text_file(input_value):
            stats = process_text_file(input_value, custom_symbol_path, skip_existing, 
                                    dry_run, output_dir, parallel)
            
            # Show summary
            total_attempted = stats["processed"] + stats["failed"]
            if total_attempted > 0:
                success_rate = (stats["processed"] / total_attempted) * 100
                print(f"\nSummary: {success_rate:.1f}% success rate")
                if stats["skipped"] > 0:
                    print(f"Skipped {stats['skipped']} existing labels")
            
            # Return appropriate exit code based on results
            if stats["failed"] > 0:
                return 1 if stats["processed"] == 0 else 0
            return 0
        else:
            logging.error(f"'{input_value}' is not a text file. Please provide a .txt file or a set code.")
            return 1
    else:
        # Treat as direct set code - always interactive for single sets
        result = create_label(input_value, custom_symbol_path, skip_existing, 
                            dry_run, output_dir, interactive=True)
        return 0 if result in ["success", "skipped"] else 1


if __name__ == "__main__":
    exit(main())
