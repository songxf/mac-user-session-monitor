#!/usr/bin/env python3

import subprocess
import time
import sys
import os
from datetime import datetime, timedelta

# Configuration constants
TARGET_USER = "xsong"
INITIAL_MAX_SESSION_TIME = 0.2  # Initial maximum allowed session time in minutes
COOLDOWN_PERIOD = 60   # Cooldown period in seconds after screen lock
RELAXATION_PERIOD = 300  # Period in seconds to gradually increase session time back to normal

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

# Function to check if Minecraft is running
def is_minecraft_running():
    """
    Check if Minecraft is currently running
    """
    try:
        # Check for Minecraft process
        result = subprocess.run(['pgrep', '-f', 'Minecraft.app'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Minecraft is running")
            return True
        
        # Also check for Java process with Minecraft title
        result = subprocess.run(['pgrep', '-f', 'java.*minecraft'], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking Minecraft status: {e}")
        return False

# Function to check if screen is locked
def is_screen_locked():
    """
    Check if the screen is currently locked using multiple methods
    """
    try:
        # First try using pmset
        result = subprocess.run(['pmset', '-g', 'sleep'], capture_output=True, text=True)
        if 'sleep 1' in result.stdout:
            return True

        # Also check using ioreg
        result = subprocess.run(['ioreg', '-r', '-k', 'DisplayPowerState'], capture_output=True, text=True)
        if 'DisplayPowerState = 0' in result.stdout:
            return True

        # Check if screensaver is active
        result = subprocess.run(['pgrep', '-f', 'ScreenSaverEngine.app'], capture_output=True, text=True)
        return result.returncode == 0

    except Exception as e:
        print(f"Error checking screen lock status: {e}")
        return False

# Function to force logout
# Function to lock the screen
def lock_screen():
    """
    Lock the screen using pmset command
    """
    try:
        # Use pmset to lock the screen
        subprocess.run(['pmset', 'displaysleepnow'])
    except Exception as e:
        print(f"Error locking screen: {e}")
        # Fallback to AppleScript if pmset fails
        try:
            subprocess.run(['osascript', '-e', 'tell application "System Events" to keystroke "q" using {command down, control down}'])
        except Exception as e:
            print(f"Error using fallback method: {e}")

# Function to check if user is locked
def is_user_locked():
    try:
        # Check if screensaver is active
        result = subprocess.run(['pgrep', '-f', 'ScreenSaverEngine.app'], capture_output=True, text=True)
        if result.returncode == 0:
            return True

        # Check if display is sleeping
        result = subprocess.run(['ioreg', '-r', '-k', 'DisplayPowerState'], capture_output=True, text=True)
        if 'DisplayPowerState = 0' in result.stdout:
            return True

        # Check if loginwindow is active (user not logged in)
        result = subprocess.run(['pgrep', '-f', 'loginwindow.app'], capture_output=True, text=True)
        return result.returncode == 0

    except Exception as e:
        print(f"Error checking lock status: {e}")
        return False

def main():
    print("\nStarting user session monitor...")
    print(f"Monitoring user: {TARGET_USER}")
    print(f"Initial max session time: {INITIAL_MAX_SESSION_TIME} minutes")
    print(f"Cooldown period: {COOLDOWN_PERIOD} seconds")
    print(f"Relaxation period: {RELAXATION_PERIOD} seconds")
    print("\nCurrent system users:")
    MAX_SESSION_TIME = INITIAL_MAX_SESSION_TIME  # Current session time limit

    # Track when we last reduced the session time
    last_reduction_time = None
    
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
                    
                    # Check if Minecraft is running
                    if is_minecraft_running():
                        print(f"[{current_time}] Minecraft is running - reducing session time")
                        # Reduce session time by 75% when Minecraft is running
                        MAX_SESSION_TIME = max(INITIAL_MAX_SESSION_TIME / 4, 0.1)  # Minimum of 0.1 minutes
                        print(f"[{current_time}] Reduced max session time to {MAX_SESSION_TIME:.1f} minutes")
                        last_reduction_time = current_time
                        relaxation_timer = current_time + timedelta(seconds=RELAXATION_PERIOD)
                    
                    # Lock screen if activity duration exceeds MAX_SESSION_TIME
                    if activity_duration >= MAX_SESSION_TIME:
                        print(f"\n[{current_time}] {TARGET_USER} has been active for too long. Locking screen...")
                        lock_screen()
                        user_logged_in = False
                        login_time = None
                        
                        # Reduce session time by half when not running Minecraft
                        MAX_SESSION_TIME = max(INITIAL_MAX_SESSION_TIME / 2, 0.1)  # Minimum of 0.1 minutes
                        print(f"[{current_time}] Reduced max session time to {MAX_SESSION_TIME:.1f} minutes")
                        last_reduction_time = current_time
                        
                        # Start relaxation timer
                        relaxation_timer = current_time + timedelta(seconds=RELAXATION_PERIOD)
                    else:
                        # Check if we should relax the session time back to normal
                        if last_reduction_time and current_time >= relaxation_timer:
                            MAX_SESSION_TIME = min(MAX_SESSION_TIME * 1.1, INITIAL_MAX_SESSION_TIME)
                            print(f"[{current_time}] Relaxing max session time to {MAX_SESSION_TIME:.1f} minutes")
                            if MAX_SESSION_TIME == INITIAL_MAX_SESSION_TIME:
                                last_reduction_time = None
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
            
            # Check if we should relax the session time back to normal
            if last_reduction_time and current_time >= relaxation_timer:
                MAX_SESSION_TIME = min(MAX_SESSION_TIME * 1.1, INITIAL_MAX_SESSION_TIME)
                print(f"[{current_time}] Relaxing max session time to {MAX_SESSION_TIME:.1f} minutes")
                if MAX_SESSION_TIME == INITIAL_MAX_SESSION_TIME:
                    last_reduction_time = None

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
