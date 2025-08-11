#!/usr/bin/env python3
"""
Demo script for the Advanced RAT Controller Category System
This script demonstrates the new category-based organization features.
"""

import json
import time
from datetime import datetime

def demo_category_system():
    """Demonstrate the category system functionality"""
    
    print("🚀 Advanced RAT Controller - Category System Demo")
    print("=" * 60)
    
    # Available categories
    categories = {
        'auth-security': {
            'title': '🔐 Authentication & Security',
            'description': 'Admin settings, security evasion, and authentication controls',
            'features': [
                'Admin password management',
                'Session timeout controls',
                'Windows Defender toggle',
                'Process hiding',
                'IP blocking',
                'Security audit logs'
            ]
        },
        'agent-persistence': {
            'title': '🤖 Agent & Persistence',
            'description': 'UAC bypass methods and persistence mechanisms',
            'features': [
                'Fodhelper UAC bypass',
                'Computer defaults bypass',
                'SLUI bypass',
                'SDCLT bypass',
                'Registry persistence',
                'Startup entries',
                'Service installation'
            ]
        },
        'streaming-communication': {
            'title': '📡 Streaming & Communication',
            'description': 'WebRTC streaming and communication controls',
            'features': [
                'Real-time video streaming',
                'Audio streaming',
                'Codec configuration',
                'Adaptive bitrate control',
                'Frame dropping',
                'Connection statistics',
                'Quality management'
            ]
        },
        'system-monitoring': {
            'title': '💻 System Monitoring',
            'description': 'Process management and system monitoring',
            'features': [
                'Process listing',
                'System information',
                'Performance monitoring',
                'Service status',
                'Event logs',
                'Process control'
            ]
        },
        'file-operations': {
            'title': '📁 File Operations',
            'description': 'Remote file management and operations',
            'features': [
                'File upload/download',
                'Directory browsing',
                'File searching',
                'File monitoring',
                'Transfer management'
            ]
        },
        'network-control': {
            'title': '🌐 Network Control',
            'description': 'Network scanning and control tools',
            'features': [
                'Network scanning',
                'Port scanning',
                'Traffic monitoring',
                'Firewall management',
                'DNS control'
            ]
        }
    }
    
    print("\n📋 Available Categories:")
    print("-" * 40)
    
    for key, category in categories.items():
        print(f"\n{category['title']}")
        print(f"  {category['description']}")
        print("  Features:")
        for feature in category['features']:
            print(f"    • {feature}")
    
    print("\n🎯 Category Benefits:")
    print("-" * 40)
    print("• Organized functionality by purpose")
    print("• Context-aware controls and metrics")
    print("• Specialized dashboards for each category")
    print("• Improved user experience and workflow")
    print("• Better resource management")
    
    print("\n🔧 Implementation Details:")
    print("-" * 40)
    print("• Dynamic content loading based on selection")
    print("• Category-specific control buttons")
    print("• Specialized metrics and visualizations")
    print("• Responsive design with glassmorphism UI")
    print("• Real-time updates and monitoring")
    
    print("\n💡 Usage Instructions:")
    print("-" * 40)
    print("1. Select a category from the dropdown menu")
    print("2. View category-specific controls in the sidebar")
    print("3. Access specialized content and metrics")
    print("4. Use category-appropriate tools and functions")
    print("5. Switch between categories as needed")
    
    print("\n🚀 Ready to launch!")
    print("=" * 60)

def demo_category_transitions():
    """Demonstrate category switching functionality"""
    
    print("\n🔄 Category Transition Demo:")
    print("-" * 40)
    
    transitions = [
        ("All Categories", "Default dashboard with general controls"),
        ("Authentication & Security", "Security-focused controls and metrics"),
        ("Agent & Persistence", "Persistence and UAC bypass tools"),
        ("Streaming & Communication", "Streaming controls and codec settings"),
        ("System Monitoring", "Process and system monitoring tools"),
        ("File Operations", "File management and transfer controls"),
        ("Network Control", "Network scanning and control tools")
    ]
    
    for i, (category, description) in enumerate(transitions, 1):
        print(f"{i:2d}. {category}")
        print(f"    → {description}")
        time.sleep(0.5)
    
    print("\n✅ All categories loaded successfully!")

if __name__ == "__main__":
    demo_category_system()
    demo_category_transitions()
    
    print(f"\n📅 Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Your Advanced RAT Controller now has a powerful category system!")