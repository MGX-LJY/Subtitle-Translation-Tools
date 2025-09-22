# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered subtitle translation tool with a PyQt6/PySide6 GUI interface. The application translates SRT subtitle files using OpenAI API, featuring concurrent processing, persistent configuration, and specialized translation prompts for adult video content.

## Architecture

This is a monolithic PyQt6/PySide6 application contained primarily in `main.py` (~378 lines). The architecture follows a traditional desktop GUI pattern:

- **Configuration Layer**: JSON-based persistent config (`main.config.json`)
- **Data Models**: `SubtitleCue` dataclass for subtitle entries
- **Worker Thread**: `TranslateWorker` QThread for async AI translation
- **GUI Layer**: PyQt6/PySide6 widgets with table-based subtitle editing
- **I/O Layer**: SRT file parsing and writing functions

## Key Components

### Core Classes
- `Config`: Configuration dataclass with API settings
- `SubtitleCue`: Subtitle entry with timing and text fields
- `TranslateWorker`: QThread for concurrent AI translation (8 channels)
- `ConfigDialog`: Settings dialog for API configuration
- `MainWindow`: Primary GUI window with file handling

### Translation Pipeline
1. **SRT Parsing**: `parse_srt()` - Converts SRT files to `SubtitleCue` objects
2. **AI Translation**: OpenAI API calls with specialized prompts
3. **Result Processing**: Real-time GUI updates with translations
4. **Export**: `write_srt()` - Saves translated subtitles to SRT format

## Dependencies

### Required Packages
```bash
pip install PySide6 openai
```

**Core Dependencies:**
- `PySide6` (6.6+) - GUI framework
- `openai` (1.0+) - OpenAI API client
- `asyncio` - Async processing (built-in)
- `logging` - Logging system (built-in)

## Running the Application

### GUI Application
```bash
python main.py
```

### Requirements
- Python 3.8+
- Valid OpenAI API key and base URL
- PySide6 and openai packages installed

## Configuration

### Configuration File
- Location: `main.config.json` (auto-generated)
- Contains: API key, base URL, model, target language
- Persistent across sessions

### Settings Dialog
Access via GUI menu to configure:
- OpenAI API key
- API base URL  
- Model selection (default: gpt-4o-mini)
- Target language (default: 中文)

## File Structure

```
├── main.py                 # Main application file (~378 lines)
├── main.config.json        # Configuration file (auto-generated)
├── translator.log          # Application logs (auto-generated)
└── .gitignore             # Git ignore rules
```

## Development Workflow

### Running the Application
```bash
# Start GUI application
python main.py

# Check dependencies
python -c "import PySide6, openai; print('Dependencies OK')"
```

### Testing Configuration
1. Launch application
2. Open Settings dialog (menu bar)
3. Enter valid API credentials
4. Test with sample SRT file

### Debugging
- Logs written to `translator.log` and console
- Use logging level INFO for standard operation
- GUI provides progress feedback during translation

## Code Architecture Details

### Translation Modes
- **translate**: Initial AI translation with specialized prompts
- **fix**: Post-processing refinement of translations

### Concurrency Model
- 8 concurrent translation channels
- Results updated in real-time to GUI table
- Sequential result ordering maintained despite async processing

### Error Handling
- API failure recovery with logging
- GUI error dialogs for user feedback
- Graceful degradation on translation failures

## Important Notes

⚠️ **API Keys**: Configuration file contains sensitive API keys - ensure `.gitignore` includes `*.config.json`

🔒 **Content Warning**: Application contains specialized prompts for adult content translation

🎯 **Single File**: Entire application logic contained in `main.py` - no modular architecture

📝 **SRT Focus**: Currently supports only SRT subtitle format

## Common Development Tasks

### Adding New Translation Providers
Modify the `TranslateWorker` class to support additional APIs beyond OpenAI.

### Extending File Format Support
Add new parser functions similar to `parse_srt()` for formats like VTT or ASS.

### GUI Enhancements
Extend the `MainWindow` class with additional PyQt6/PySide6 widgets.

### Configuration Options
Add new fields to the `Config` dataclass and update `ConfigDialog`.