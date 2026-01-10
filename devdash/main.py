import json
import random
import time
import sys
import tty
import termios
import os
from datetime import timedelta, datetime
from collections import defaultdict
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_PATH = Path.home() / '.devdash.json'

DEFAULT_CONFIG = {
    'tab_spaces': 2,
    'show_live_stats': True,
}

def get_data_path():
    """Get the path to data.txt in the script directory."""
    return SCRIPT_DIR / 'data.txt'

def get_problems_path():
    """Get the path to problems.json in the script directory."""
    return SCRIPT_DIR / 'problems.json'

def load_config():
    """Load configuration from ~/.devdash.json or return defaults."""
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                user_config = json.load(f)
                config.update(user_config)
        except (json.JSONDecodeError, IOError):
            pass  # Use defaults if config is invalid
    return config

def save_default_config():
    """Save default configuration to ~/.devdash.json if it doesn't exist."""
    if not CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Created config file: {CONFIG_PATH}")

# ANSI color codes - using standard codes for compatibility
class Colors:
    WHITE = '\033[0m\033[97m'  # Bright white text
    GREEN = '\033[0m\033[92m'  # Bright green text
    RED = '\033[0m\033[91m'  # Bright red text
    YELLOW = '\033[0m\033[93m'  # Bright yellow text
    DIM = '\033[0m\033[90m'  # Bright black (gray) text
    ORANGE = '\033[0m\033[33m'  # Yellow (closest to orange in standard ANSI)

    # Backgrounds
    BG_RED = '\033[41m'  # Red background
    BG_ORANGE = '\033[43m'  # Yellow background (closest to orange)
    BG_CLEAR = '\033[49m'  # Clear background

    # Special combinations
    CURSOR_HIGHLIGHT = '\033[0m\033[43m\033[30m'  # Yellow bg + black text
    ERROR_HIGHLIGHT = '\033[0m\033[41m\033[97m'  # Red bg + bright white text

def clear_screen():
    print('\033[2J\033[H\033[0m\033[97m', end='')  # Clear screen, reset, set bright white text

def get_terminal_height():
    """Get the terminal height in lines."""
    return os.get_terminal_size().lines

def load_random_problem():
    """Load a random problem from the JSON file."""
    problems_path = get_problems_path()
    with open(problems_path, 'r') as f:
        data = json.load(f)
    # Filter out empty problem lists
    data = [p for p in data if p and len(p) > 0]
    if not data:
        raise ValueError("No valid problems found in JSON file")
    problem_list = random.choice(data)
    problem = problem_list[0]
    return problem['id'], problem['code']

def get_char():
    """Get a single character from stdin without waiting for Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return char

def display_header(problem_id, stats=None):
    """Display the header with problem information and live stats."""
    print(f"{Colors.DIM}{'─'*70}")
    if stats:
        elapsed_str = f"{int(stats['elapsed']//60)}:{int(stats['elapsed']%60):02d}"
        accuracy_color = Colors.GREEN if stats['accuracy'] >= 95 else Colors.YELLOW if stats['accuracy'] >= 85 else Colors.RED
        print(f"{Colors.YELLOW}  {problem_id:<40} {Colors.DIM}│ {Colors.WHITE}CPM: {Colors.GREEN}{stats['cpm']:>3.0f} {Colors.DIM}│ {accuracy_color}Acc: {stats['accuracy']:>5.1f}% {Colors.DIM}│ {Colors.WHITE}{elapsed_str}")
    else:
        print(f"{Colors.YELLOW}  {problem_id}")
    print(f"{Colors.DIM}{'─'*70}")

def calculate_scroll_window(target_text, current_pos, terminal_height):
    """Calculate which lines to display based on cursor position for smooth scrolling."""
    lines = target_text.split('\n')

    # Reserve lines for header (5 lines)
    header_lines = 5
    available_lines = terminal_height - header_lines

    # Find which line the cursor is on
    char_count = 0
    cursor_line = 0
    for line_idx, line in enumerate(lines):
        if char_count + len(line) >= current_pos:
            cursor_line = line_idx
            break
        char_count += len(line) + 1  # +1 for newline

    # Calculate the window with cursor roughly in the middle
    center_offset = available_lines // 2
    start_line = max(0, cursor_line - center_offset)
    end_line = min(len(lines), start_line + available_lines)

    # Adjust if we're at the end
    if end_line == len(lines):
        start_line = max(0, end_line - available_lines)

    return start_line, end_line

def display_text_with_cursor(target_text, typed_text, current_pos):
    """Display the target text with color-coded typed characters and cursor, IDE-style."""
    print('\033[H\033[J', end='')  # Clear screen and move to top

    lines = target_text.split('\n')
    terminal_height = get_terminal_height()
    start_line, end_line = calculate_scroll_window(target_text, current_pos, terminal_height)
    total_lines = len(lines)
    line_num_width = len(str(total_lines))

    char_count = 0
    # Calculate char_count offset for start_line
    for i in range(start_line):
        char_count += len(lines[i]) + 1  # +1 for newline

    # Find which line cursor is on for highlighting
    cursor_char_count = 0
    cursor_line = 0
    for idx, line in enumerate(lines):
        if cursor_char_count + len(line) >= current_pos:
            cursor_line = idx
            break
        cursor_char_count += len(line) + 1

    for line_idx in range(start_line, end_line):
        line = lines[line_idx]
        line_num = line_idx + 1

        # Line number gutter - highlight current line
        if line_idx == cursor_line:
            gutter = f"{Colors.YELLOW}{line_num:>{line_num_width}} {Colors.DIM}│ "
        else:
            gutter = f"{Colors.DIM}{line_num:>{line_num_width}} │ "

        output = gutter
        for char_idx, char in enumerate(line):
            abs_pos = char_count + char_idx

            # Convert tabs to 4 spaces for display
            display_char = '    ' if char == '\t' else char

            if abs_pos < len(typed_text):
                if typed_text[abs_pos] == char:
                    output += f"{Colors.WHITE}{display_char}"  # Correct chars are white
                else:
                    # Show the incorrect character with red highlight
                    wrong_char = typed_text[abs_pos]
                    display_wrong = '    ' if wrong_char == '\t' else ('·' if wrong_char == ' ' else wrong_char)
                    output += f"{Colors.ERROR_HIGHLIGHT}{display_wrong}"
            elif abs_pos == current_pos:
                # Highlight current character cell with cursor
                if char == ' ':
                    output += f"{Colors.CURSOR_HIGHLIGHT} "
                else:
                    output += f"{Colors.CURSOR_HIGHLIGHT}{display_char}"
            else:
                output += f"{Colors.DIM}{display_char}"

        # Check if cursor is at end of line (for Enter key)
        end_of_line_pos = char_count + len(line)
        if end_of_line_pos == current_pos and line_idx < len(lines) - 1:
            output += f"{Colors.CURSOR_HIGHLIGHT}↵"

        print(output + Colors.WHITE)
        char_count += len(line)

        # Account for newline character
        if line_idx < len(lines) - 1:
            char_count += 1

def calculate_metrics(target_text, typed_text, elapsed_time, all_typed_chars, wrong_typed_chars):
    """Calculate typing metrics."""
    total_chars = len(target_text)
    typed_chars = len(typed_text)
    correct_chars = sum(1 for i, c in enumerate(typed_text) if i < len(target_text) and c == target_text[i])

    minutes = elapsed_time / 60

    # Accuracy: correct keystrokes / total keystrokes (capped at 100%)
    accuracy = min(100.0, (correct_chars / all_typed_chars * 100)) if all_typed_chars > 0 else 0

    # CPM: Characters Per Minute (correct characters only)
    cpm = correct_chars / minutes if minutes > 0 else 0

    return {
        'total_chars': total_chars,
        'typed_chars': typed_chars,
        'correct_chars': correct_chars,
        'all_typed_chars': all_typed_chars,
        'wrong_typed_chars': wrong_typed_chars,
        'cpm': cpm,
        'accuracy': accuracy,
        'time': elapsed_time
    }

def display_results(metrics, missed_chars):
    """Display final results."""
    clear_screen()
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.ORANGE}RESULTS")
    print(f"{Colors.ORANGE}{'='*80}")
    print(f"{Colors.WHITE}Time Elapsed: {timedelta(seconds=int(metrics['time']))}")
    print(f"{Colors.WHITE}Characters Per Minute (CPM): {Colors.GREEN}{metrics['cpm']:.0f}")
    print(f"{Colors.WHITE}Accuracy: {Colors.GREEN if metrics['accuracy'] >= 95 else Colors.YELLOW}{metrics['accuracy']:.1f}%")
    print(f"{Colors.WHITE}Character Breakdown:")
    print(f"{Colors.WHITE}  Target Characters: {metrics['total_chars']}")
    print(f"{Colors.WHITE}  {Colors.GREEN}Correct: {metrics['correct_chars']}")
    print(f"{Colors.WHITE}  {Colors.RED}Wrong: {metrics['wrong_typed_chars']}")
    print(f"{Colors.WHITE}  Total Typed: {metrics['all_typed_chars']}")

    if missed_chars:
        print(f"\n{Colors.WHITE}Most Missed Characters:")
        sorted_missed = sorted(missed_chars.items(), key=lambda x: x[1], reverse=True)
        for char, count in sorted_missed[:10]:  # Show top 10
            display_char = repr(char) if char in ('\n', '\t', ' ') else char
            print(f"{Colors.WHITE}  {Colors.RED}{display_char}: {count}")


def save_to_data_file(metrics):
    """Save metrics to data.txt file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data_path = get_data_path()
    with open(data_path, 'a') as f:
        f.write(f"{timestamp},{metrics['cpm']:.0f},{metrics['accuracy']:.2f},{metrics['time']:.2f}\n")

def plot_terminal():
    """Plot CPM and accuracy vs time in the terminal."""
    try:
        data_path = get_data_path()
        with open(data_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            print(f"{Colors.YELLOW}No data to plot yet.")
            return

        # Parse data
        cpms = []
        accuracies = []
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                cpms.append(float(parts[1]))
                accuracies.append(float(parts[2]))

        if not cpms:
            print(f"{Colors.YELLOW}No valid data to plot.")
            return

        # Terminal plot dimensions
        plot_width = 30
        plot_height = 15

        # Normalize data for plotting
        max_cpm = max(cpms) if cpms else 1
        max_accuracy = 100  # Accuracy is always 0-100

        print(f"\n{Colors.ORANGE}{'='*80}")
        print(f"{Colors.ORANGE}PROGRESS OVER TIME")
        print(f"{Colors.ORANGE}{'='*80}\n")

        # Plot header
        print(f"{Colors.WHITE}       CPM                                 Accuracy (%)")

        # Plot both graphs side by side
        for row in range(plot_height, 0, -1):
            cpm_threshold = (row / plot_height) * max_cpm
            acc_threshold = (row / plot_height) * max_accuracy

            # CPM side
            line = f"{Colors.DIM}{cpm_threshold:5.0f} {Colors.WHITE}│"
            for i, cpm in enumerate(cpms[-plot_width:]):
                if cpm >= cpm_threshold:
                    line += f"{Colors.GREEN}▇"
                else:
                    line += f"{Colors.DIM}·"

            # Spacing
            line += f"{Colors.WHITE}  "

            # Accuracy side
            line += f"{Colors.DIM}{acc_threshold:5.1f} {Colors.WHITE}│"
            for i, acc in enumerate(accuracies[-plot_width:]):
                if acc >= acc_threshold:
                    line += f"{Colors.GREEN}▇"
                else:
                    line += f"{Colors.DIM}·"

            print(line)

        # Bottom axis
        print(f"{Colors.DIM}      └{'─' * min(len(cpms), plot_width)}  {'      └'}{'─' * min(len(accuracies), plot_width)}")

        print(f"\n{Colors.DIM}Showing last {min(len(cpms), plot_width)} runs")
        print(f"{Colors.ORANGE}{'='*80}\n")

    except FileNotFoundError:
        print(f"{Colors.YELLOW}No data file found yet. Complete a test to start tracking progress.")

def get_live_stats(start_time, typed_text, target_text, all_typed_chars, wrong_typed_chars):
    """Calculate live statistics during typing."""
    if start_time is None:
        return {'cpm': 0, 'accuracy': 100.0, 'elapsed': 0}

    elapsed = time.time() - start_time
    minutes = elapsed / 60

    correct_chars = sum(1 for i, c in enumerate(typed_text) if i < len(target_text) and c == target_text[i])
    cpm = correct_chars / minutes if minutes > 0 else 0
    accuracy = min(100.0, (correct_chars / all_typed_chars * 100)) if all_typed_chars > 0 else 100.0

    return {'cpm': cpm, 'accuracy': accuracy, 'elapsed': elapsed}

def main():
    config = load_config()

    try:
        # Load problem
        problem_id, target_text = load_random_problem()

        clear_screen()
        display_header(problem_id)

        # Initialize
        typed_text = ""
        start_time = None  # Will start on first key press
        current_pos = 0
        all_typed_chars = 0  # Track all characters typed including deleted ones
        wrong_typed_chars = 0  # Track characters that were typed incorrectly
        missed_chars = defaultdict(int)  # Track which characters were missed
        paused = False
        pause_start = None
        total_pause_time = 0

        # Main typing loop
        while current_pos < len(target_text):
            # Calculate live stats
            stats = None
            if start_time is not None and config.get('show_live_stats', True):
                stats = get_live_stats(start_time, typed_text, target_text, all_typed_chars, wrong_typed_chars)

            display_header(problem_id, stats)
            display_text_with_cursor(target_text, typed_text, current_pos)

            char = get_char()

            # Handle pause (Escape key)
            if ord(char) == 27:  # Escape
                if start_time is not None:
                    paused = True
                    pause_start = time.time()
                    clear_screen()
                    print(f"\n{Colors.YELLOW}  PAUSED")
                    print(f"{Colors.DIM}  Press any key to continue...")
                    get_char()  # Wait for any key
                    total_pause_time += time.time() - pause_start
                    paused = False
                continue

            # Start timer on first keypress
            if start_time is None:
                start_time = time.time()

            # Handle special keys
            if ord(char) == 3:  # Ctrl+C
                raise KeyboardInterrupt
            elif ord(char) == 127:  # Backspace
                if typed_text:
                    # Check if we're removing a correct or wrong character
                    removed_pos = current_pos - 1
                    if removed_pos >= 0 and removed_pos < len(target_text):
                        was_correct = typed_text[removed_pos] == target_text[removed_pos]
                        # Don't penalize - just remove the character
                    typed_text = typed_text[:-1]
                    current_pos = max(0, current_pos - 1)
            elif char == '\t':  # Tab key
                tab_spaces = config.get('tab_spaces', 2)
                typed_text += ' ' * tab_spaces
                all_typed_chars += tab_spaces
                # Check if these characters are correct
                for i in range(current_pos, min(current_pos + tab_spaces, len(target_text))):
                    if i >= len(target_text) or typed_text[i] != target_text[i]:
                        wrong_typed_chars += 1
                        if i < len(target_text):
                            missed_chars[target_text[i]] += 1
                current_pos += tab_spaces
            elif char == '\n' or char == '\r':  # Enter key - IDE-like auto-indent
                # Find the next line's leading whitespace in target_text
                next_line_start = current_pos + 1
                if next_line_start < len(target_text):
                    next_line_end = target_text.find('\n', next_line_start)
                    if next_line_end == -1:
                        next_line_end = len(target_text)
                    next_line = target_text[next_line_start:next_line_end]

                    # Get the target's leading whitespace for the next line
                    target_indent = ''
                    for c in next_line:
                        if c in ('\t', ' '):
                            target_indent += c
                        else:
                            break

                    # Auto-fill newline + target indentation
                    auto_fill = '\n' + target_indent
                else:
                    auto_fill = '\n'

                typed_text += auto_fill
                all_typed_chars += 1  # Only count Enter as 1 keystroke (indent is auto)
                # Check correctness for the newline character only
                if current_pos >= len(target_text) or target_text[current_pos] != '\n':
                    wrong_typed_chars += 1
                    if current_pos < len(target_text):
                        missed_chars[target_text[current_pos]] += 1
                current_pos += len(auto_fill)
            else:
                typed_text += char
                all_typed_chars += 1
                # Check if this character is correct
                if current_pos >= len(target_text) or char != target_text[current_pos]:
                    wrong_typed_chars += 1
                    if current_pos < len(target_text):
                        missed_chars[target_text[current_pos]] += 1
                current_pos += 1

        # Calculate elapsed time (subtract pause time)
        elapsed_time = time.time() - start_time - total_pause_time

        # Calculate and display metrics
        metrics = calculate_metrics(target_text, typed_text, elapsed_time, all_typed_chars, wrong_typed_chars)
        display_results(metrics, missed_chars)

        # Save to data file
        save_to_data_file(metrics)

        # Plot progress
        plot_terminal()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test cancelled.")
        sys.exit(0)
    except FileNotFoundError:
        print(f"{Colors.RED}Error: problems.json not found!")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()