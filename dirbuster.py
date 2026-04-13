#!/usr/bin/env python3
import requests
import sys
import threading
from urllib.parse import urljoin
from datetime import datetime
import argparse
import time

# Renk kodları
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
PURPLE = '\033[95m'
RESET = '\033[0m'

def banner():
    print(f"""
{BLUE}╔══════════════════════════════════════════╗
║   Dobivorn Directory Buster 🐉           ║
║   Web Dizin/Dosya Tarayıcı               ║
╚══════════════════════════════════════════╝{RESET}
    """)

def load_wordlist(file_path):
    """Wordlist dosyasını okur"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        return words
    except FileNotFoundError:
        print(f"{RED}[!] Wordlist bulunamadı: {file_path}{RESET}")
        sys.exit(1)

def test_path(base_url, path, timeout=5):
    """Belirtilen yolu test et"""
    url = urljoin(base_url, path)
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=False)
        
        if response.status_code == 200:
            print(f"{GREEN}[✓] {url} -> {response.status_code}{RESET}")
            return (url, response.status_code)
        elif response.status_code in [301, 302]:
            print(f"{BLUE}[→] {url} -> {response.status_code} (Yönlendirme){RESET}")
            return (url, response.status_code)
        elif response.status_code == 403:
            print(f"{PURPLE}[!] {url} -> {response.status_code} (Yasak){RESET}")
            return (url, response.status_code)
        elif response.status_code == 404:
            # Sessiz geç, ekrana yazma
            return None
        else:
            print(f"{YELLOW}[?] {url} -> {response.status_code}{RESET}")
            return (url, response.status_code)
    except requests.exceptions.Timeout:
        print(f"{RED}[!] {url} -> Zaman aşımı{RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] {url} -> Bağlantı hatası{RESET}")
    except Exception as e:
        print(f"{RED}[!] {url} -> Hata: {str(e)[:50]}{RESET}")
    return None

def scan_worker(base_url, paths, timeout, results, thread_id):
    """Thread çalışanı"""
    for path in paths:
        result = test_path(base_url, path, timeout)
        if result:
            results.append(result)

def scan_directory(base_url, wordlist, threads=10, timeout=5):
    """Çoklu thread ile tarama yap"""
    print(f"{YELLOW}[+] Hedef: {base_url}{RESET}")
    print(f"[+] Wordlist: {len(wordlist)} kelime")
    print(f"[+] Thread: {threads}")
    print(f"[+] Başlangıç: {datetime.now()}\n")
    
    # Kelimeleri thread'lere böl
    chunk_size = len(wordlist) // threads + 1
    chunks = [wordlist[i:i+chunk_size] for i in range(0, len(wordlist), chunk_size)]
    
    results = []
    thread_list = []
    
    # Thread'leri başlat
    for i, chunk in enumerate(chunks):
        t = threading.Thread(target=scan_worker, args=(base_url, chunk, timeout, results, i))
        thread_list.append(t)
        t.start()
    
    # Thread'lerin bitmesini bekle
    for t in thread_list:
        t.join()
    
    # Özet göster
    print(f"\n{BLUE}╔══════════════════════════════════════════╗")
    print(f"║              TARAMA ÖZETİ                 ║")
    print(f"╚══════════════════════════════════════════╝{RESET}")
    print(f"{YELLOW}[+] Hedef: {base_url}{RESET}")
    print(f"[+] Taranan: {len(wordlist)}")
    print(f"{GREEN}[+] Bulunan: {len(results)}{RESET}")
    
    if results:
        print(f"\n{GREEN}Bulunan dizin/dosyalar:{RESET}")
        for url, code in results:
            print(f"  → {code} : {url}")
    
    print(f"\n{YELLOW}[+] Bitiş: {datetime.now()}{RESET}")

def main():
    banner()
    
    parser = argparse.ArgumentParser(description="Dobivorn Directory Buster - Web Dizin Tarayıcı")
    parser.add_argument("url", help="Hedef URL (örn: https://example.com)")
    parser.add_argument("-w", "--wordlist", default="wordlists/common.txt", help="Wordlist dosyası")
    parser.add_argument("-t", "--threads", type=int, default=10, help="Thread sayısı (varsayılan: 10)")
    parser.add_argument("-to", "--timeout", type=int, default=5, help="Zaman aşımı saniye (varsayılan: 5)")
    
    args = parser.parse_args()
    
    # URL'yi düzenle
    base_url = args.url.rstrip('/') + '/'
    
    # Wordlist'i yükle
    wordlist = load_wordlist(args.wordlist)
    
    # Tarama başlat
    scan_directory(base_url, wordlist, args.threads, args.timeout)

if __name__ == "__main__":
    main()
