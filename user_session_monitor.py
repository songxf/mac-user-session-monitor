#!/usr/bin/env python3

import subprocess
import time
import sys
import os
from datetime import datetime, timedelta

# Configuration constants
TARGET_USER = "xsong"
MAX_SESSION_TIME = 10  # Maximum allowed session time in minutes
COOLDOWN_PERIOD = 60   # Cooldown period in seconds after screen lock

# Function to check if user is actively using mouse/keyboard
def is_user_active(user):
    """
    Check if a user is actively using their session by checking if they are the console user
    """
    try:
        # Check if user is the current console user
        result = subprocess.run(['stat', '-f%Su', '/dev/console'], capture_output=True, text=True)
        print(f"\nConsole user: {result.stdout.strip()}")
        return user in result.stdout
    except Exception as e:
        print(f"Error checking user activity: {e}")
        return False

# Function to check if screen is locked
def is_screen_locked():
    """
    Check if the screen is currently locked
    """
    try:
        result = subprocess.run(['ioreg', '-r', '-k', 'DisplayPowerState'], capture_output=True, text=True)
        return 'DisplayPowerState = 0' in result.stdout
    except Exception as e:
        print(f"Error checking screen lock status: {e}")
        return False

# Function to force logout
# Function to lock the screen
def lock_screen():
    """
    Lock the screen using pmset
    """
    try:
        subprocess.run(['pmset', 'displaysleepnow'])
    except Exception as e:
        print(f"Error locking screen: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error locking screen: {e}")

# Function to check if user is locked
def is_user_locked():
    try:
        result = subprocess.run(['pgrep', '-f', 'ScreenSaverEngine.app'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking lock status: {e}")
        return False

def main():
    print("\nStarting user session monitor...")
    print(f"Monitoring user: {TARGET_USER}")
    print(f"Max session time: {MAX_SESSION_TIME} minutes")
    print(f"Cooldown period: {COOLDOWN_PERIOD} seconds")
    print("\nCurrent system users:")
    
    # Ensure we're running with admin privileges
    if os.geteuid() != 0:
        print("\nError: This script must be run as root")
        sys.exit(1)

    # Get initial list of logged in users
    try:
        result = subprocess.run(['who', '-u'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error getting initial user list: {e}")

    user_logged_in = False
    login_time = None
    last_lock_time = None

    # Print configuration summary
    print("\nMonitoring configuration:")
    print(f"Target user: {TARGET_USER}")
    print(f"Max session time: {MAX_SESSION_TIME} minutes")
    print(f"Cooldown period: {COOLDOWN_PERIOD} seconds")
    print("\nMonitoring started...")
    print("-" * 50)

    while True:
        try:
            current_time = datetime.now()
            
            # Check if target user is active
            if is_user_active(TARGET_USER):
                # Update activity time
                if user_logged_in:
                    activity_duration = (current_time - login_time).total_seconds() / 60
                    print(f"\n[{current_time}] {TARGET_USER} has been active for {activity_duration:.1f} minutes")
                    
                    # Lock screen if activity duration exceeds MAX_SESSION_TIME
                    if activity_duration >= MAX_SESSION_TIME:
                        print(f"\n[{current_time}] {TARGET_USER} has been active for too long. Locking screen...")
                        subprocess.run(['pmset', 'displaysleepnow'])
                        user_logged_in = False
                        login_time = None
                else:
                    # User just became active
                    user_logged_in = True
                    login_time = current_time
                    print(f"\n[{current_time}] {TARGET_USER} is now active")
            else:
                # User is inactive
                if user_logged_in:
                    print(f"\n[{current_time}] {TARGET_USER} is now inactive")
                user_logged_in = False
                login_time = None

            # Wait before next check
            time.sleep(1)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

            print("\n" + "-" * 50)  # Separator
            time.sleep(10)  # Check every 10 seconds for better activity detection

        except KeyboardInterrupt:
            print("\n\nStopping user session monitor...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(5)  # Wait before retrying

        except KeyboardInterrupt:
            print("\nStopping user session monitor...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    main()
