#!/usr/bin/env python3

import subprocess
import time
import sys
import os
from datetime import date
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Configuration constants
TARGET_USER = "hsong"
MAX_SESSION_TIME = 900  # Maximum allowed session time in seconds
daily_active_times = {}

# Load environment variables
load_dotenv()

# Slack configuration
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')  # Set this in your .env file
print(SLACK_BOT_TOKEN)
SLACK_CHANNEL = "mac_control"  # Change this to your desired channel
SLACK_NOTIFICATION_INTERVAL = 600  # Send notifications every 10 minutes (600 seconds)

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


def get_current_date():
    """Get the current date as a string"""
    return str(date.today())

def update_daily_active_time(seconds):
    """
    Update the daily active time by the specified number of seconds
    """
    try:
        try:
            date_str = get_current_date()
        except Exception as date_error:
            print(f"Error getting current date: {date_error}")
            return None
        
        # Get or initialize today's active time
        if date_str not in daily_active_times:
            daily_active_times[date_str] = 0
        
        # Update active time
        daily_active_times[date_str] += seconds
        
        return daily_active_times[date_str]
    except Exception as e:
        print(f"Error updating daily active time: {e}")
        return None

def send_slack_notification(message):
    """
    Send a notification to Slack channel
    """
    if not SLACK_BOT_TOKEN:
        print("Warning: Slack bot token not configured. Skipping notification.")
        return

    try:
        client = WebClient(token=SLACK_BOT_TOKEN)
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        if not response["ok"]:
            print(f"Error sending Slack notification: {response['error']}")
    except SlackApiError as e:
        print(f"Error sending message: {e}")

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

    loop_time = 2
    today_active_time = 0 
    last_slack_notification = time.time() - 3600
    while True:
        try:
            # Get current active user
            result = subprocess.run(['stat', '-f%Su', '/dev/console'], capture_output=True, text=True)
            active_user = result.stdout.strip()
            message = f"\nActive user: {active_user} - Target User: {TARGET_USER} with daily active time {today_active_time:.0f}/{MAX_SESSION_TIME} seconds"
            print(message)
            
            if is_user_active(TARGET_USER):
                today_active_time = update_daily_active_time(loop_time)
                if today_active_time >= MAX_SESSION_TIME:
                    current_time = time.time()
                    if current_time - last_slack_notification >= SLACK_NOTIFICATION_INTERVAL:
                        message1 = f"Daily active time limit exceeded for user {TARGET_USER}. Active time: {today_active_time:.0f}s / {MAX_SESSION_TIME}s"
                        print(message1)
                        message = message + "\n" + message1
                    lock_screen()
            current_time = time.time()
            if current_time - last_slack_notification >= SLACK_NOTIFICATION_INTERVAL:
                send_slack_notification(message)
                last_slack_notification = current_time
            time.sleep(loop_time)
        except KeyboardInterrupt:
            print("\n\nStopping user session monitor...")
            break

if __name__ == "__main__":
    main()
