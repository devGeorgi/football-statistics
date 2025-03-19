import os
from datetime import datetime

class MatchLogger:
    """Class to handle logging of match processing information"""
    
    def __init__(self, log_file="skipped_matches.log"):
        """Initialize the logger with a file path"""
        self.log_file_path = log_file
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Create the log directory if it doesn't exist"""
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def log_skipped_match(self, date, home_team, away_team, reason="unplayed/postponed"):
        """Log information about a skipped match"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Date: {date} - {home_team} vs {away_team} - Reason: {reason}\n"
        
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)

def get_logger(log_file="skipped_matches.log"):
    """Factory function to create a logger instance"""
    return MatchLogger(log_file)
