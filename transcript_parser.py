import re
import csv
import json
import webvtt
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd


class TranscriptParser:
    """
    Format-agnostic transcript parser that extracts todos from meeting transcripts.
    Supports VTT, SRT, TXT, and JSON formats.
    """
    
    def __init__(self):
        self.todo_keywords = [
            r'(?i)\btodo\b',
            r'(?i)\baction\s+item\b',
            r'(?i)\bneed\s+to\b',
            r'(?i)\bwill\s+do\b',
            r'(?i)\bshould\s+do\b',
            r'(?i)\bmust\s+do\b',
            r'(?i)\bhave\s+to\b',
            r'(?i)\bgoing\s+to\b',
            r'(?i)\bwill\s+handle\b',
            r'(?i)\bwill\s+take\s+care\s+of\b',
            r'(?i)\bwill\s+work\s+on\b',
            r'(?i)\bresponsible\s+for\b',
            r'(?i)\bassigned\s+to\b'
        ]
        
        self.assignment_patterns = [
            r'(?i)([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(will|needs?\s+to|should|must|has\s+to)\s+(.+?)(?:\.|$)',
            r'(?i)([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(is\s+(?:going\s+to|responsible\s+for))\s+(.+?)(?:\.|$)',
            r'(?i)(assign(?:ed)?\s+to|give\s+to)\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)[:\s]+(.+?)(?:\.|$)'
        ]
    
    def detect_format(self, file_path: str) -> str:
        """Detect the format of the transcript file."""
        extension = file_path.lower().split('.')[-1]
        
        if extension in ['vtt', 'webvtt']:
            return 'vtt'
        elif extension == 'srt':
            return 'srt'
        elif extension == 'json':
            return 'json'
        else:
            return 'txt'
    
    def parse_vtt(self, file_path: str) -> List[Dict]:
        """Parse VTT format transcript."""
        captions = []
        try:
            vtt = webvtt.read(file_path)
            for caption in vtt:
                captions.append({
                    'timestamp': caption.start,
                    'speaker': self._extract_speaker_from_text(caption.text),
                    'text': caption.text
                })
        except Exception as e:
            print(f"Error parsing VTT file: {e}")
        return captions
    
    def parse_srt(self, file_path: str) -> List[Dict]:
        """Parse SRT format transcript."""
        captions = []
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # SRT format parsing
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                timestamp = lines[1]
                text = ' '.join(lines[2:])
                captions.append({
                    'timestamp': timestamp.split(' --> ')[0],
                    'speaker': self._extract_speaker_from_text(text),
                    'text': text
                })
        return captions
    
    def parse_txt(self, file_path: str) -> List[Dict]:
        """Parse plain text transcript."""
        captions = []
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                captions.append({
                    'timestamp': f"Line {i+1}",
                    'speaker': self._extract_speaker_from_text(line),
                    'text': line
                })
        return captions
    
    def parse_json(self, file_path: str) -> List[Dict]:
        """Parse JSON format transcript (Teams export format)."""
        captions = []
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Handle different JSON structures
        if isinstance(data, list):
            for item in data:
                captions.append({
                    'timestamp': item.get('timestamp', item.get('start', 'Unknown')),
                    'speaker': item.get('speaker', item.get('name', 'Unknown')),
                    'text': item.get('text', item.get('content', ''))
                })
        elif isinstance(data, dict) and 'transcript' in data:
            for item in data['transcript']:
                captions.append({
                    'timestamp': item.get('timestamp', 'Unknown'),
                    'speaker': item.get('speaker', 'Unknown'),
                    'text': item.get('text', '')
                })
        
        return captions
    
    def _extract_speaker_from_text(self, text: str) -> str:
        """Extract speaker name from text if present."""
        # Common patterns: "John Doe: text" or "[John Doe] text"
        speaker_patterns = [
            r'^([A-Za-z\s]+):\s*',
            r'^\[([A-Za-z\s]+)\]\s*',
            r'^<([A-Za-z\s]+)>\s*'
        ]
        
        for pattern in speaker_patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(1).strip()
        
        return 'Unknown'
    
    def _normalize_todo_text(self, todo_text: str) -> str:
        """Normalize todo text for deduplication by removing common prefixes and suffixes."""
        # Remove common prefixes like "I will", "be", etc.
        todo_text = re.sub(r'^(I\s+will\s+|be\s+|to\s+|responsible\s+for\s+)', '', todo_text, flags=re.IGNORECASE).strip()
        # Remove trailing punctuation and whitespace
        todo_text = re.sub(r'[.!?]+$', '', todo_text).strip()
        # Remove extra whitespace
        todo_text = re.sub(r'\s+', ' ', todo_text)
        return todo_text.lower()
    
    def _is_similar_todo(self, new_todo: str, existing_todos: List[str], threshold: float = 0.5) -> bool:
        """Check if a new todo is similar to any existing todos using word overlap."""
        # Normalize both todos for better comparison
        new_normalized = self._normalize_todo_text(new_todo)
        new_words = set(new_normalized.split())
        if len(new_words) == 0:
            return False
            
        for existing_todo in existing_todos:
            existing_normalized = self._normalize_todo_text(existing_todo)
            existing_words = set(existing_normalized.split())
            if len(existing_words) == 0:
                continue
                
            # Calculate Jaccard similarity (intersection over union)
            intersection = new_words.intersection(existing_words)
            union = new_words.union(existing_words)
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                if similarity >= threshold:
                    return True
        return False
    
    def extract_todos(self, captions: List[Dict]) -> List[Dict]:
        """Extract todos from parsed captions."""
        todos = []
        todos_by_speaker_context = {}  # Group todos by (speaker, context) for similarity checking
        
        for caption in captions:
            text = caption['text']
            speaker = caption['speaker']
            timestamp = caption['timestamp']
            
            speaker_context_key = (speaker, text)
            if speaker_context_key not in todos_by_speaker_context:
                todos_by_speaker_context[speaker_context_key] = []
            
            # Check for todo keywords
            for keyword_pattern in self.todo_keywords:
                matches = re.finditer(keyword_pattern, text)
                for match in matches:
                    # Extract sentence after the keyword
                    start_pos = match.end()
                    remaining_text = text[start_pos:].strip()
                    
                    # Find the sentence (until period or end of text)
                    sentence_match = re.match(r'[:\s]*([^.!?]*[.!?]?)', remaining_text)
                    if sentence_match:
                        todo_text = sentence_match.group(1).strip()
                        if todo_text and len(todo_text) > 3:  # Filter out very short matches
                            # Check if this todo is similar to existing ones for same speaker/context
                            existing_todos = [t['todo'] for t in todos_by_speaker_context[speaker_context_key]]
                            
                            if not self._is_similar_todo(todo_text, existing_todos):
                                new_todo = {
                                    'timestamp': timestamp,
                                    'speaker': speaker,
                                    'keyword': match.group(0),
                                    'todo': todo_text,
                                    'assignee': self._extract_assignee(text),
                                    'context': text
                                }
                                todos.append(new_todo)
                                todos_by_speaker_context[speaker_context_key].append(new_todo)
            
            # Check for assignment patterns
            for pattern in self.assignment_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 3:
                        if pattern.startswith('(?i)(assign'):
                            assignee = groups[1].strip()
                            todo_text = groups[2].strip()
                        else:
                            assignee = groups[0].strip()
                            todo_text = groups[2].strip()
                        
                        if todo_text and len(todo_text) > 3:
                            # Check if this todo is similar to existing ones for same speaker/context
                            existing_todos = [t['todo'] for t in todos_by_speaker_context[speaker_context_key]]
                            
                            if not self._is_similar_todo(todo_text, existing_todos):
                                new_todo = {
                                    'timestamp': timestamp,
                                    'speaker': speaker,
                                    'keyword': 'assignment',
                                    'todo': todo_text,
                                    'assignee': assignee,
                                    'context': text
                                }
                                todos.append(new_todo)
                                todos_by_speaker_context[speaker_context_key].append(new_todo)
        
        return todos
    
    def _extract_assignee(self, text: str) -> str:
        """Extract assignee from text if present."""
        # Look for names after assignment keywords
        assignment_patterns = [
            r'(?i)assign(?:ed)?\s+to\s+([A-Za-z\s]+)',
            r'(?i)([A-Za-z\s]+)\s+will\s+',
            r'(?i)([A-Za-z\s]+)\s+should\s+',
            r'(?i)([A-Za-z\s]+)\s+needs?\s+to\s+'
        ]
        
        for pattern in assignment_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return 'Unassigned'
    
    def save_to_csv(self, todos: List[Dict], output_file: str):
        """Save extracted todos to CSV file."""
        if not todos:
            print("No todos found to save.")
            return
        
        df = pd.DataFrame(todos)
        df.to_csv(output_file, index=False)
        print(f"Saved {len(todos)} todos to {output_file}")
    
    def parse_transcript(self, file_path: str, output_file: str = None) -> List[Dict]:
        """Main method to parse transcript and extract todos."""
        format_type = self.detect_format(file_path)
        print(f"Detected format: {format_type}")
        
        # Parse based on format
        if format_type == 'vtt':
            captions = self.parse_vtt(file_path)
        elif format_type == 'srt':
            captions = self.parse_srt(file_path)
        elif format_type == 'json':
            captions = self.parse_json(file_path)
        else:
            captions = self.parse_txt(file_path)
        
        print(f"Parsed {len(captions)} captions")
        
        # Extract todos
        todos = self.extract_todos(captions)
        print(f"Found {len(todos)} potential todos")
        
        # Save to CSV if output file specified
        if output_file:
            self.save_to_csv(todos, output_file)
        
        return todos