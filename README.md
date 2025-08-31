# MTG Label Generator

A Python tool for generating professional-looking labels for Magic: The Gathering card sets. Creates PNG images with set symbols, names, codes, and release dates.

The design is adjusted for a 16mm wide label which is commonly used on thermal printers.

## Features

- **Automatic Set Information**: Fetches set data from Scryfall API
- **Set Symbol Integration**: Downloads and scales set symbols automatically
- **Custom Symbols**: Support for custom symbol images
- **Batch Processing**: Process multiple sets from text files
- **Resilient Operation**: Retry logic for network requests and graceful error handling
- **Skip Existing**: Option to skip labels that already exist
- **Dry Run Mode**: Preview what would be generated without creating files
- **Progress Tracking**: Beautiful progress bars with timing information
- **Flexible Output**: Configurable verbosity levels and output directories
- **Set Discovery**: List recent MTG sets to find codes easily
- **Validation Mode**: Check set codes without generating labels
- **Parallel Processing**: Optional parallel processing for large batches
- **Smart Confirmation**: User prompts for potentially risky operations
- **Interactive Symbol Handling**: Prompts for missing symbols with multiple options
- **Comprehensive Statistics**: Detailed success/failure reporting

## Installation

1. Clone or download this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Generate a single label:
```bash
python labels.py AFR
```

Process multiple sets from a file:
```bash
python labels.py sets.txt
```

### Command Line Options

```bash
python labels.py [INPUT] [OPTIONS]
```

**Arguments:**
- `INPUT`: Set code (e.g., `AFR`) or path to `.txt` file containing set codes (optional for some commands)

**Options:**
- `-s, --symbol PATH`: Use custom symbol image instead of downloading
- `-o, --output-dir DIR`: Output directory for generated labels (default: ./labels)
- `--skip`: Skip generating labels that already exist
- `--dry-run`: Show what would be generated without creating files
- `-v, --verbose`: Show detailed output and progress information
- `-q, --quiet`: Suppress all output except errors
- `-f, --force`: Overwrite existing labels (opposite of --skip)
- `-p, --parallel N`: Process N sets in parallel (use with caution for large batches)
- `--list-recent`: List recent MTG sets with their codes
- `--validate`: Validate set codes without generating labels

### Examples

```bash
# Generate label for Adventures in the Forgotten Realms
python labels.py AFR

# Process all sets from file, skipping existing labels
python labels.py sets.txt --skip

# Use a custom symbol image
python labels.py AFR -s custom_symbol.png

# Preview what would be generated without creating files
python labels.py sets.txt --dry-run

# Verbose output for debugging
python labels.py AFR --verbose

# Quiet mode (errors only)
python labels.py sets.txt --quiet

# Force overwrite existing labels
python labels.py sets.txt --force

# List recent MTG sets to find codes
python labels.py --list-recent

# Validate set codes without generating labels
python labels.py --validate sets.txt

# Use custom output directory
python labels.py AFR -o /path/to/output

# Process sets in parallel (use carefully)
python labels.py sets.txt -p 3
```

## Input File Format

Create a text file with one set code per line:

```
AFR
DOM
WAR
ELD
THB
```

See `sets.txt` for a comprehensive example with many MTG sets.

## Output

Labels are saved as PNG files in the `./labels/` directory with the format:
```
{SET_CODE}_label.png
```

Each label includes:
- Set symbol (scaled to fit)
- Set name (auto-sized font)
- Set code and release date

## Error Handling

The tool includes robust error handling:

- **Network Issues**: Automatic retry with exponential backoff
- **Rate Limiting**: Respects API rate limits with appropriate delays
- **Missing Sets**: Continues processing other sets if one fails
- **Invalid Data**: Validates set information before processing
- **File Errors**: Graceful handling of missing files or permissions

## Exit Codes

- `0`: Success (all operations completed successfully)
- `1`: Failure (one or more operations failed)

## Project Structure

The tool is organized into several modules for better maintainability:

- `labels.py`: Main entry point and CLI orchestration
- `cli.py`: Command line argument parsing and logging setup
- `mtg_api.py`: API operations for fetching set data and symbols
- `image_generator.py`: Image creation and processing logic
- `label_processor.py`: Core label processing and file handling

## Dependencies

- `requests`: HTTP requests for API calls
- `Pillow`: Image processing and generation
- `argparse`: Command line argument parsing (built-in)
- `logging`: Logging functionality (built-in)

## API Usage

This tool uses the [Scryfall API](https://scryfall.com/docs/api) to fetch set information and [MTG Collection Builder](https://mtgcollectionbuilder.com/) for set symbols.

## Troubleshooting

### Common Issues

**"Set not found" errors:**
- Use `--list-recent` to see available set codes
- Use `--validate` to check if your set codes are correct
- Verify the set code is correct and exists on Scryfall

**Network timeouts:**
- Check your internet connection
- The tool will automatically retry failed requests
- Try reducing parallel processing (`-p` flag) if using it

**Permission errors:**
- Ensure you have write permissions in the output directory
- Use `-o` to specify a different output directory
- The tool creates output folders automatically

**Symbol not found:**
- The tool will prompt you to provide a custom symbol or skip the set
- For batch processing, you can choose to handle all missing symbols the same way
- Some older or special sets may not have symbols available online
- Use the `--symbol` option to provide a custom symbol for all sets

**Performance issues:**
- Use `--skip` to avoid regenerating existing labels
- Try parallel processing with `-p` for large batches (but watch for rate limits)
- Use `--dry-run` first to estimate processing time

### Getting Help

**Find set codes:**
```bash
python labels.py --list-recent
```

**Validate your input:**
```bash
python labels.py --validate sets.txt
```

**Debug issues:**
```bash
python labels.py AFR --verbose
```

This shows:
- API requests and responses
- File operations
- Retry attempts
- Symbol loading details
- Progress timing

## Contributing

Feel free to submit issues or pull requests to improve the tool. Some areas for enhancement:

- Additional output formats (PDF, SVG)
- Configurable label dimensions and styling
- Caching for offline operation
- GUI interface

## License

This project is provided as-is for personal use. Respect the terms of service for the APIs used (Scryfall, MTG Collection Builder).
