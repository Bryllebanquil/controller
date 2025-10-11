#!/usr/bin/env python3
"""
Test Notification Generator for Agent-Controller UI v2.1

This script helps you test the notification system by triggering various types of notifications.
Run this alongside your controller to see notifications appear in real-time.

Usage:
    python test_notifications.py
"""

import requests
import json
import time
import sys
from getpass import getpass

# Configuration
CONTROLLER_URL = "http://localhost:8080"
SESSION_COOKIE = None

def login(password):
    """Login to get session cookie"""
    global SESSION_COOKIE
    try:
        response = requests.post(
            f"{CONTROLLER_URL}/api/auth/login",
            json={"password": password},
            allow_redirects=False
        )
        
        if response.status_code == 200 or 'session' in response.cookies:
            SESSION_COOKIE = response.cookies.get('session')
            print("✅ Login successful!")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def send_test_notification(notif_type, title, message, category):
    """Send a test notification"""
    try:
        cookies = {'session': SESSION_COOKIE} if SESSION_COOKIE else {}
        response = requests.post(
            f"{CONTROLLER_URL}/api/test/notification",
            json={
                "type": notif_type,
                "title": title,
                "message": message,
                "category": category
            },
            cookies=cookies
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Notification sent: {title}")
                return True
        
        print(f"❌ Failed to send notification: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False

def get_notifications():
    """Fetch current notifications"""
    try:
        cookies = {'session': SESSION_COOKIE} if SESSION_COOKIE else {}
        response = requests.get(
            f"{CONTROLLER_URL}/api/notifications?limit=10",
            cookies=cookies
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                notifications = data.get('notifications', [])
                print(f"\n📊 Current Notifications: {len(notifications)}")
                print(f"📬 Unread: {data.get('unread_count', 0)}")
                return notifications
        
        print(f"❌ Failed to get notifications: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        return []

def get_notification_stats():
    """Get notification statistics"""
    try:
        cookies = {'session': SESSION_COOKIE} if SESSION_COOKIE else {}
        response = requests.get(
            f"{CONTROLLER_URL}/api/notifications/stats",
            cookies=cookies
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('stats', {})
                print("\n📈 Notification Statistics:")
                print(f"   Total: {stats.get('total', 0)}")
                print(f"   Unread: {stats.get('unread', 0)}")
                print(f"   Read: {stats.get('read', 0)}")
                print(f"   By Category: {stats.get('by_category', {})}")
                print(f"   By Type: {stats.get('by_type', {})}")
                return stats
        
        print(f"❌ Failed to get stats: {response.status_code}")
        return None
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

def run_test_suite():
    """Run a comprehensive test suite"""
    print("\n🧪 Running Notification Test Suite...\n")
    
    tests = [
        {
            "type": "success",
            "title": "Test Success",
            "message": "This is a success notification test",
            "category": "system"
        },
        {
            "type": "info",
            "title": "Test Info",
            "message": "This is an informational notification",
            "category": "system"
        },
        {
            "type": "warning",
            "title": "Test Warning",
            "message": "This is a warning notification",
            "category": "security"
        },
        {
            "type": "error",
            "title": "Test Error",
            "message": "This is an error notification",
            "category": "security"
        },
        {
            "type": "success",
            "title": "Agent Test",
            "message": "Simulated agent connection",
            "category": "agent"
        },
        {
            "type": "warning",
            "title": "Agent Disconnect",
            "message": "Simulated agent disconnection",
            "category": "agent"
        },
        {
            "type": "info",
            "title": "Command Test",
            "message": "Command execution completed",
            "category": "command"
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}] Testing: {test['type'].upper()} - {test['title']}")
        send_test_notification(
            test['type'],
            test['title'],
            test['message'],
            test['category']
        )
        time.sleep(1)  # Wait between notifications
    
    print("\n✅ Test suite completed!")
    time.sleep(2)
    get_notification_stats()

def interactive_mode():
    """Interactive mode for manual testing"""
    while True:
        print("\n" + "="*50)
        print("🔔 Notification Test Menu")
        print("="*50)
        print("1. Send custom notification")
        print("2. Run test suite (7 notifications)")
        print("3. View recent notifications")
        print("4. View notification stats")
        print("5. Send success notification")
        print("6. Send warning notification")
        print("7. Send error notification")
        print("8. Send info notification")
        print("9. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (1-9): ").strip()
        
        if choice == '1':
            print("\nNotification Types: success, warning, error, info")
            notif_type = input("Type: ").strip() or "info"
            print("\nCategories: agent, system, security, command")
            category = input("Category: ").strip() or "system"
            title = input("Title: ").strip() or "Test Notification"
            message = input("Message: ").strip() or "Test message"
            send_test_notification(notif_type, title, message, category)
        
        elif choice == '2':
            run_test_suite()
        
        elif choice == '3':
            notifications = get_notifications()
            if notifications:
                print("\n📋 Recent Notifications:")
                for notif in notifications[:5]:
                    status = "🔴" if not notif.get('read') else "✅"
                    print(f"   {status} [{notif['type'].upper()}] {notif['title']}: {notif['message']}")
        
        elif choice == '4':
            get_notification_stats()
        
        elif choice == '5':
            send_test_notification('success', 'Success Test', 'Operation completed successfully', 'system')
        
        elif choice == '6':
            send_test_notification('warning', 'Warning Test', 'Warning: Check system status', 'security')
        
        elif choice == '7':
            send_test_notification('error', 'Error Test', 'Error: Operation failed', 'system')
        
        elif choice == '8':
            send_test_notification('info', 'Info Test', 'Information: System update', 'system')
        
        elif choice == '9':
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        else:
            print("\n❌ Invalid choice!")

def main():
    print("="*50)
    print("🔔 Agent-Controller UI v2.1 Notification Tester")
    print("="*50)
    
    # Check if test endpoint exists
    print("\n⚠️  NOTE: This script requires the test endpoint to be added to controller.py")
    print("See NOTIFICATION_TRIGGER_GUIDE.md for instructions.\n")
    
    # Get controller URL
    global CONTROLLER_URL
    url_input = input(f"Controller URL (default: {CONTROLLER_URL}): ").strip()
    if url_input:
        CONTROLLER_URL = url_input.rstrip('/')
    
    # Login
    password = getpass("Admin password: ")
    if not login(password):
        print("\n❌ Authentication failed. Please check your password.")
        sys.exit(1)
    
    # Start interactive mode
    interactive_mode()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
