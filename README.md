# devdash

A terminal-based typing speed test designed for Python developers. Practice typing real code from LeetCode problems while tracking your progress over time.

## Features

- **Real Code Practice**: Type actual Python solutions from 499 LeetCode problems
- **Live Statistics**: See your CPM (Characters Per Minute) and accuracy in real-time
- **IDE-like Experience**: Line numbers, auto-indentation on Enter, smart cursor
- **Progress Tracking**: Historical data with terminal-based graphs
- **Pause Support**: Press `Esc` to pause without losing progress
- **Configurable**: Customize settings via `~/.devdash.json`

## Installation

```bash
pip install devdashh
```

## Usage

```bash
devdash
```

Or run as a module:

```bash
python -m devdash
```

### Controls

| Key | Action |
|-----|--------|
| Any key | Start typing (timer begins on first keypress) |
| `Backspace` | Delete previous character |
| `Tab` | Insert spaces (configurable, default: 2) |
| `Enter` | New line with auto-indentation |
| `Esc` | Pause/Resume |
| `Ctrl+C` | Quit |

## Configuration

Create `~/.devdash.json` to customize settings:

```json
{
  "tab_spaces": 2,
  "show_live_stats": true
}
```

### Options

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `tab_spaces` | int | 2 | Number of spaces inserted when pressing Tab |
| `show_live_stats` | bool | true | Show CPM/accuracy in header while typing |

## Metrics

- **CPM (Characters Per Minute)**: Correct characters typed per minute
- **Accuracy**: Percentage of correct keystrokes (capped at 100%)

## Data Storage

Your typing history is stored in `data.txt` in the package directory with the format:
```
timestamp,cpm,accuracy,elapsed_seconds
```

## Requirements

- Python 3.8+
- macOS or Linux (uses `termios` for terminal input)

## License

MIT
