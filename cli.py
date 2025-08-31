"""Command line interface for the MTG label generator."""

import argparse
import logging
import os
from typing import Optional


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate labels for Magic: The Gathering card sets.",
        epilog="""
Examples:
  %(prog)s AFR                    # Generate label for Adventures in the Forgotten Realms
  %(prog)s sets.txt               # Process all sets from file
  %(prog)s sets.txt --skip        # Skip existing labels
  %(prog)s AFR -s custom.png      # Use custom symbol
  %(prog)s sets.txt --dry-run     # Preview what would be generated
  %(prog)s AFR --verbose          # Show detailed output
  %(prog)s --list-recent          # Show recent MTG sets
  %(prog)s --validate sets.txt    # Check if set codes are valid
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="A set code (e.g., AFR) or a path to a .txt file containing set codes.",
    )
    parser.add_argument(
        "--symbol",
        "-s",
        help="Path to a custom symbol image file to use instead of fetching from the web.",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Skip generating labels that already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating files.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output and progress information.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors.",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing labels (opposite of --skip).",
    )
    parser.add_argument(
        "--list-recent",
        action="store_true",
        help="List recent MTG sets with their codes.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate set codes without generating labels.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./labels",
        help="Output directory for generated labels (default: ./labels).",
    )
    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        metavar="N",
        help="Process N sets in parallel (default: sequential).",
    )
    return parser.parse_args()


def setup_logging(verbose: bool, quiet: bool):
    """Setup logging configuration based on verbosity flags."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )


def is_text_file(filename: str) -> bool:
    """Check if a filename has a .txt extension."""
    return filename.lower().endswith(".txt")


def get_terminal_width() -> int:
    """Get terminal width for better formatting."""
    try:
        import shutil
        return shutil.get_terminal_size().columns
    except:
        return 80


def print_progress_bar(current: int, total: int, prefix: str = "", suffix: str = "", 
                      length: int = 50, fill: str = '█', empty: str = '░') -> None:
    """Print a progress bar to the terminal."""
    if total == 0:
        return
    
    percent = current / total
    filled_length = int(length * percent)
    bar = fill * filled_length + empty * (length - filled_length)
    
    # Calculate percentage
    percentage = f"{percent:.1%}"
    
    # Format the progress line
    progress_line = f"\r{prefix} |{bar}| {current}/{total} {percentage} {suffix}"
    
    # Truncate if too long for terminal
    terminal_width = get_terminal_width()
    if len(progress_line) > terminal_width:
        progress_line = progress_line[:terminal_width-3] + "..."
    
    print(progress_line, end='', flush=True)


def format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    try:
        response = input(f"{message}{suffix}: ").strip().lower()
        if not response:
            return default
        return response in ['y', 'yes', 'true', '1']
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def prompt_for_symbol(set_code: str, set_name: str) -> Optional[str]:
    """Prompt user for a custom symbol when none is found."""
    print(f"\n⚠️  No symbol found for {set_code} ({set_name})")
    print("Options:")
    print("  1. Provide a custom symbol image path")
    print("  2. Skip this set")
    print("  3. Continue without symbol (create text-only label)")
    
    try:
        while True:
            choice = input("Choose an option [1/2/3]: ").strip()
            
            if choice == "1":
                symbol_path = input("Enter path to symbol image: ").strip()
                if symbol_path and os.path.exists(symbol_path):
                    return symbol_path
                elif symbol_path:
                    print(f"File not found: {symbol_path}")
                    continue
                else:
                    continue
            elif choice == "2":
                return "SKIP"
            elif choice == "3":
                return "NO_SYMBOL"
            else:
                print("Please enter 1, 2, or 3")
                
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user")
        return "SKIP"


def prompt_for_symbol_batch(set_code: str, set_name: str, remaining_count: int) -> str:
    """Prompt user for symbol handling in batch mode with additional options."""
    print(f"\n⚠️  No symbol found for {set_code} ({set_name})")
    print(f"   {remaining_count} sets remaining in batch")
    print("Options:")
    print("  1. Provide custom symbol for this set")
    print("  2. Skip this set only")
    print("  3. Continue without symbol for this set")
    print("  4. Skip ALL remaining sets without symbols")
    print("  5. Continue without symbols for ALL remaining sets")
    
    try:
        while True:
            choice = input("Choose an option [1/2/3/4/5]: ").strip()
            
            if choice == "1":
                symbol_path = input("Enter path to symbol image: ").strip()
                if symbol_path and os.path.exists(symbol_path):
                    return f"CUSTOM:{symbol_path}"
                elif symbol_path:
                    print(f"File not found: {symbol_path}")
                    continue
                else:
                    continue
            elif choice == "2":
                return "SKIP"
            elif choice == "3":
                return "NO_SYMBOL"
            elif choice == "4":
                return "SKIP_ALL_NO_SYMBOL"
            elif choice == "5":
                return "NO_SYMBOL_ALL"
            else:
                print("Please enter 1, 2, 3, 4, or 5")
                
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user")
        return "SKIP"
