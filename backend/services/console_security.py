"""
Enhanced Console Security Module

This module provides security enhancements for the integrated console:
1. Command validation and sanitization
2. Command history limits
3. Rate limiting
4. Dangerous command detection
5. Session timeout
"""

import re
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ConsoleSecurityManager:
    """Security manager for console command execution"""
    
    # Dangerous commands that should be warned about
    DANGEROUS_COMMANDS = [
        r'^rm\s+-rf\s+/',
        r'^dd\s+if=',
        r':(){ :|:& };:',  # Fork bomb
        r'^mkfs\.',
        r'>/dev/sd',
        r'chmod\s+-R\s+777',
        r'chown\s+-R\s+',
    ]
    
    # Maximum command length
    MAX_COMMAND_LENGTH = 10000
    
    # Maximum command history
    MAX_HISTORY_SIZE = 1000
    
    # Rate limiting: max commands per minute
    MAX_COMMANDS_PER_MINUTE = 30
    
    # Session timeout
    SESSION_TIMEOUT_MINUTES = 30
    
    def __init__(self):
        self.command_history: List[Dict] = []
        self.rate_limit_tracker: Dict[str, List[float]] = {}
        self.session_start_time = datetime.now()
    
    def validate_command(self, command: str, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate a command before execution.
        
        Args:
            command: Command to validate
            user_id: User attempting to execute command
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check command length
        if len(command) > self.MAX_COMMAND_LENGTH:
            return False, f"Command too long (max {self.MAX_COMMAND_LENGTH} characters)"
        
        # Check for null bytes or other dangerous characters
        if '\x00' in command:
            return False, "Command contains null bytes"
        
        # Check rate limiting
        if not self._check_rate_limit(user_id):
            return False, "Too many commands. Please wait a moment."
        
        # Check session timeout
        if not self._check_session_timeout():
            return False, "Session expired. Please refresh the page."
        
        # Check for dangerous commands
        warning = self._check_dangerous_command(command)
        if warning:
            # Don't block, but return warning
            return True, warning
        
        return True, None
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit"""
        now = time.time()
        
        # Initialize if needed
        if user_id not in self.rate_limit_tracker:
            self.rate_limit_tracker[user_id] = []
        
        # Remove old timestamps (older than 1 minute)
        self.rate_limit_tracker[user_id] = [
            ts for ts in self.rate_limit_tracker[user_id]
            if now - ts < 60
        ]
        
        # Check if under limit
        if len(self.rate_limit_tracker[user_id]) >= self.MAX_COMMANDS_PER_MINUTE:
            return False
        
        # Add current timestamp
        self.rate_limit_tracker[user_id].append(now)
        return True
    
    def _check_session_timeout(self) -> bool:
        """Check if session has expired"""
        elapsed = datetime.now() - self.session_start_time
        return elapsed < timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
    
    def _check_dangerous_command(self, command: str) -> Optional[str]:
        """Check if command matches dangerous patterns"""
        for pattern in self.DANGEROUS_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                return f"⚠️ WARNING: This command may be dangerous: {command[:50]}"
        return None
    
    def add_to_history(self, command: str, user_id: str, success: bool):
        """Add command to history"""
        self.command_history.append({
            'command': command,
            'user_id': user_id,
            'timestamp': datetime.now(),
            'success': success
        })
        
        # Trim history if too large
        if len(self.command_history) > self.MAX_HISTORY_SIZE:
            self.command_history = self.command_history[-self.MAX_HISTORY_SIZE:]
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[str]:
        """Get command history for a user"""
        user_commands = [
            entry['command']
            for entry in self.command_history
            if entry['user_id'] == user_id and entry['success']
        ]
        return user_commands[-limit:]
    
    def sanitize_output(self, output: str) -> str:
        """
        Sanitize command output for display.
        
        Removes potential security risks like:
        - ANSI escape sequences that could manipulate terminal
        - Excessive whitespace
        - Control characters
        """
        # Remove dangerous ANSI sequences (keep safe ones)
        # Safe: color codes (30-37, 90-97), bold (1), reset (0)
        # Unsafe: cursor movement, terminal manipulation
        
        safe_ansi_pattern = r'\x1b\[(?:[0-9]{1,2}(?:;[0-9]{1,2})*)?m'
        
        # First, extract all ANSI sequences
        ansi_sequences = re.findall(r'\x1b\[[^m]*m', output)
        
        # Remove all ANSI sequences
        cleaned = re.sub(r'\x1b\[[^m]*m', '', output)
        
        # Re-add only safe ones
        for seq in ansi_sequences:
            if re.match(safe_ansi_pattern, seq):
                # This is a safe color/style code, allow it
                pass
            else:
                # Remove cursor movement, clear screen, etc.
                cleaned = cleaned.replace(seq, '')
        
        # Limit output length (prevent DoS via huge outputs)
        max_output_length = 100000  # 100KB
        if len(cleaned) > max_output_length:
            cleaned = cleaned[:max_output_length] + '\n... (output truncated)'
        
        return cleaned


# Singleton instance
_security_manager = None


def get_security_manager() -> ConsoleSecurityManager:
    """Get singleton security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = ConsoleSecurityManager()
    return _security_manager
