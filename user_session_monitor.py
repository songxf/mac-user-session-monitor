#!/usr/bin/env python3

import subprocess
import time
import sys
import os
from datetime import date

# Configuration constants
TARGET_USER = "hsong"
MAX_SESSION_TIME = 900  # Maximum allowed session time in seconds
daily_active_times = {}

def is_user_active(user):
    """
    Check if a user is actively using their session by checking if they are the console user
    """
    try:
        result = subprocess.run(['stat', '-f%Su', '/dev/console'], capture_output=True, text=True)
        return user in result.stdout
    except Exception as e:
        print(f"Error checking user activity: {e}")
        return False


def update_daily_active_time(seconds):
    """
    Update the daily active time by the specified number of seconds
    """
    try:
        current_date = date.today()
        if str(current_date) not in daily_active_times:
            daily_active_times[str(current_date)] = 0
        daily_active_times[str(current_date)] += seconds
        return daily_active_times[str(current_date)]
    except Exception as e:
        print(f"Error updating daily active time: {e}")
        return None

def lock_screen():
    """
    Lock the screen using pmset command
    """
    try:
        subprocess.run(['pmset', 'displaysleepnow'])
    except Exception as e:
        print(f"Error locking screen: {e}")
        try:
            subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "q" using {command down, control down}'])
        except Exception as e:
            print(f"Error using fallback method: {e}")

def main():
    print("\nStarting user session monitor...")
    print(f"Monitoring user: {TARGET_USER}")
    print(f"Max session time: {MAX_SESSION_TIME} seconds")
    
    if os.geteuid() != 0:
        print("\nError: This script must be run as root")
        sys.exit(1)

    print("\nMonitoring configuration:")
    print(f"Target user: {TARGET_USER}")

    loop_time = 1
    today_active_time = 0 
    while True:
        try:
            # Get current active user
            result = subprocess.run(['stat', '-f%Su', '/dev/console'], capture_output=True, text=True)
            active_user = result.stdout.strip()
            print(f"\nActive user: {active_user} - Target User: {TARGET_USER} with daily active time {today_active_time:.1f} seconds")
            
            if is_user_active(TARGET_USER):
                today_active_time = update_daily_active_time(loop_time)
                print(f"Daily active time: {today_active_time:.1f} seconds")
                if today_active_time >= MAX_SESSION_TIME:
                    print(f"Daily active time limit exceeded ({today_active_time:.1f} seconds). Locking screen...")
                    lock_screen()
            time.sleep(loop_time)
        except KeyboardInterrupt:
            print("\n\nStopping user session monitor...")
            break

if __name__ == "__main__":
    main()
