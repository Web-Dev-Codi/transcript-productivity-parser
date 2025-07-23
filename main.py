#!/usr/bin/env python3
"""
Transcript Todo Parser - CLI Interface
Extract todos from Microsoft Teams meeting transcripts and export to CSV.
"""

import argparse
import sys
import os
from transcript_parser import TranscriptParser


def main():
    parser = argparse.ArgumentParser(
        description="Extract todos from meeting transcripts and save to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py transcript.vtt
  python main.py transcript.txt -o todos.csv
  python main.py meeting.json --output meeting_todos.csv
  
Supported formats: VTT, SRT, TXT, JSON
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the transcript file'
    )
    
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Output CSV file path (default: input_filename_todos.csv)'
    )
    
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview todos without saving to file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed parsing information'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Generate output filename if not provided
    if not args.output and not args.preview:
        base_name = os.path.splitext(args.input_file)[0]
        args.output = f"{base_name}_todos.csv"
    
    # Initialize parser
    transcript_parser = TranscriptParser()
    
    try:
        # Parse transcript
        if args.verbose:
            print(f"Processing: {args.input_file}")
        
        todos = transcript_parser.parse_transcript(
            args.input_file, 
            args.output if not args.preview else None
        )
        
        # Preview mode
        if args.preview:
            print("\n=== PREVIEW OF EXTRACTED TODOS ===")
            if not todos:
                print("No todos found in the transcript.")
            else:
                for i, todo in enumerate(todos, 1):
                    print(f"\n{i}. [{todo['timestamp']}] {todo['speaker']}")
                    print(f"   Keyword: {todo['keyword']}")
                    print(f"   Todo: {todo['todo']}")
                    print(f"   Assignee: {todo['assignee']}")
                    if args.verbose:
                        print(f"   Context: {todo['context']}")
        
        # Summary
        print(f"\nSummary:")
        print(f"- Found {len(todos)} todos")
        if not args.preview and args.output:
            print(f"- Saved to: {args.output}")
        
    except Exception as e:
        print(f"Error processing transcript: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()