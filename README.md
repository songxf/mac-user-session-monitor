# Mac User Session Monitor

A Python script that monitors user sessions on macOS and automatically locks the screen if a specific user exceeds their allowed session time.

## Features

- Monitors user login sessions
- Locks the screen after a configurable timeout period
- Implements a cooldown period before allowing login again
- Detailed logging of user sessions and state changes
- Runs with admin privileges

## Requirements

- Python 3.x
- macOS
- Admin privileges

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

## Usage

Run the script with admin privileges:
```bash
sudo python user_session_monitor.py
```

## Configuration

The script can be configured by modifying these constants in the code:
- `TARGET_USER`: The user to monitor
- `MAX_SESSION_TIME`: Maximum allowed session time in minutes
- `COOLDOWN_PERIOD`: Time in seconds before allowing login after screen lock

## License

MIT License
