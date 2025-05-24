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
    Check if a user is actively using their session by detecting mouse and keyboard activity
    """
    try:
        # Check if user is logged in
        result = subprocess.run(['who', '-u'], capture_output=True, text=True)
        if user not in result.stdout:
            print(f"User {user} is not logged in")
            return False

        # Check if user has any active processes
        result = subprocess.run(['ps', '-u', user], capture_output=True, text=True)
        if len(result.stdout.splitlines()) > 1:  # More than header line means active processes
            print(f"User {user} has active processes:")
            print(result.stdout)
            return True

        # Check if user has any active windows
        result = subprocess.run(['lsappinfo', 'info', '--name', user], capture_output=True, text=True)
        if user in result.stdout:
            print(f"User {user} has active windows")
            return True

        # Check if user has any active sessions
        result = subprocess.run(['lslogin', '-u', user], capture_output=True, text=True)
        if user in result.stdout:
            print(f"User {user} has active sessions")
            return True

        print(f"User {user} is inactive")
        return False
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
    try:
        print("Locking screen...")
        subprocess.run(['pmset', 'displaysleepnow'], check=True)
        print("Screen locked successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error locking screen: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

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

    while True:
        try:
            current_time = datetime.now()
            current_users = []
            
            # Get current list of logged in users
            try:
                result = subprocess.run(['who', '-u'], capture_output=True, text=True)
                print(f"\n[{current_time}] Current users:")
                print(result.stdout)
            except Exception as e:
                print(f"Error getting user list: {e}")

            # Check if target user is actively using their session
            if is_user_active(TARGET_USER):
                # Log activity details
                try:
                    result = subprocess.run(['ioreg', '-r', '-k', 'HIDIdleTime'], capture_output=True, text=True)
                    idle_time = None
                    for line in result.stdout.splitlines():
                        if 'HIDIdleTime' in line:
                            parts = line.split('=')
                            if len(parts) > 1:
                                idle_time = int(parts[1].strip())
                                break
                    
                    if idle_time is not None:
                        print(f"\n[{current_time}] {TARGET_USER} idle time: {idle_time/1000000:.1f} seconds")
                except Exception as e:
                    print(f"Error getting idle time: {e}")

                if not user_logged_in:
                    # User just became active
                    user_logged_in = True
                    login_time = current_time
                    print(f"\n[{current_time}] {TARGET_USER} became active")
                    print(f"Session start time: {login_time}")
                else:
                    # User already active, check duration
                    duration = current_time - login_time
                    print(f"\n[{current_time}] {TARGET_USER} active duration: {duration.total_seconds():.1f} seconds")
                    
                    if duration.total_seconds() > MAX_SESSION_TIME * 60:
                        print(f"\n[{current_time}] {TARGET_USER} active session exceeded {MAX_SESSION_TIME} minutes")
                        print(f"Locking screen...")
                        lock_screen()
                        last_lock_time = current_time
                        print(f"Screen locked at {current_time}")
                        user_logged_in = False
                        login_time = None
            else:
                if user_logged_in:
                    print(f"\n[{current_time}] {TARGET_USER} became inactive")
                user_logged_in = False
                login_time = None

            # If screen is locked, check if we should unlock
            if last_lock_time:
                cooldown_time = current_time - last_lock_time
                print(f"\n[{current_time}] Lock cooldown: {cooldown_time.total_seconds()} seconds")
                if cooldown_time.total_seconds() > COOLDOWN_PERIOD:
                    if not is_screen_locked():
                        print(f"\n[{current_time}] Screen is no longer locked")
                        last_lock_time = None
                    else:
                        print(f"\n[{current_time}] Screen still locked")
                if not user_logged_in:
                    # User just became active
                    user_logged_in = True
                    login_time = current_time
                    print(f"\n[{current_time}] {TARGET_USER} became active")
                    print(f"Session start time: {login_time}")
                    
                    # Get active processes
                    try:
                        result = subprocess.run(['ps', '-u', TARGET_USER], capture_output=True, text=True)
                        print(f"\nActive processes for {TARGET_USER}:")
                        print(result.stdout)
                    except Exception as e:
                        print(f"Error getting process list: {e}")
                else:
                    # User already logged in, check duration
                    duration = current_time - login_time
                    print(f"\n[{current_time}] {TARGET_USER} session duration: {duration.total_seconds()} seconds")
                    
                    if duration.total_seconds() > MAX_SESSION_TIME * 60:
                        print(f"\n[{current_time}] {TARGET_USER} session exceeded {MAX_SESSION_TIME} minutes")
                        print(f"Locking screen...")
                        lock_screen()
                        last_lock_time = current_time
                        print(f"Screen locked at {current_time}")
                        user_logged_in = False
                        login_time = None
            else:
                user_logged_in = False
                login_time = None

            # If screen is locked, check if we should unlock
            if last_lock_time:
                cooldown_time = current_time - last_lock_time
                print(f"\n[{current_time}] Lock cooldown: {cooldown_time.total_seconds()} seconds")
                if cooldown_time.total_seconds() > COOLDOWN_PERIOD:
                    print(f"\n[{current_time}] Lock cooldown period expired")
                    last_lock_time = None

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
