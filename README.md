# Transcript Todo Parser

A format-agnostic Python tool that extracts todo items and action items from Microsoft Teams meeting transcripts and exports them to CSV format.

## Features

- **Format Agnostic**: Supports VTT, SRT, TXT, and JSON transcript formats
- **Intelligent Extraction**: Identifies todos using multiple keyword patterns and context analysis  
- **Speaker Detection**: Automatically extracts speaker names from transcripts
- **Assignment Recognition**: Identifies who is assigned to each todo item
- **CSV Export**: Outputs structured data with timestamp, speaker, todo text, and assignee
- **CLI Interface**: Easy-to-use command line interface with preview mode

## Installation

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python main.py transcript.vtt
python main.py meeting_notes.txt -o todos.csv
```

### Preview Mode (without saving)
```bash
python main.py transcript.txt --preview
```

### Verbose Output
```bash
python main.py transcript.vtt --verbose -o detailed_todos.csv
```

## Supported Keywords

The parser automatically detects todos when speakers use these keywords:
- "todo", "action item"
- "need to", "have to", "must do"
- "will do", "should do", "going to"
- "will handle", "will work on", "will take care of"
- "responsible for", "assigned to"

## Output Format

The CSV output includes these columns:
- **timestamp**: When the todo was mentioned
- **speaker**: Who mentioned the todo
- **keyword**: The trigger keyword found
- **todo**: The extracted todo text
- **assignee**: Who is assigned (if identified)
- **context**: Full context of the statement

## Examples

Run with the provided sample files:
```bash
python main.py example_transcript.txt --preview
python main.py example_teams.vtt -o sample_output.csv
```

## Supported Formats

- **VTT/WebVTT**: Microsoft Teams and other video platform exports
- **SRT**: Subtitle format files
- **TXT**: Plain text transcripts with speaker identification
- **JSON**: Structured transcript data