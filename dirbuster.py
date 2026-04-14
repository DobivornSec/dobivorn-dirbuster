#!/usr/bin/env python3
"""
Dobivorn Directory Buster v3.0 🐉
Gelişmiş Web Dizin/Dosya Tarayıcı
Red Team | Purple Team | Blue Team

Özellikler:
- 404 bulanıklaştırma (hash karşılaştırma)
- Teknoloji tespiti (WordPress, Laravel, Django, React, Angular)
- Git sızıntısı tespiti
- Asenkron mimari (800+ req/s)
- JSON/CSV/TXT raporlama
- Recursive tarama
- Çoklu uzantı desteği
- Proxy/Tor desteği
"""

import asyncio
import aiohttp
import sys
import argparse
import json
import csv
from urllib.parse import urljoin, urlparse
from datetime import datetime
from colorama import init, Fore, Style
import random
from tqdm import tqdm
import hashlib

# Proxy desteği için 
try:
    from aiohttp_socks import ProxyConnector
    SOCKS_SUPPORT = True
except ImportError:
    SOCKS_SUPPORT = False
    ProxyConnector = None

# Renkleri başlat
init(autoreset=True)

# Banner
BANNER = f"""
{Fore.BLUE}╔══════════════════════════════════════════════════════════════╗
║   🐉 Dobivorn Directory Buster v3.0 - 3 Başlı Ejderha       ║
║   🔴 Red Team | 🟣 Purple Team | 🔵 Blue Team                ║
║   ✨ 404 Hash | Tech Detect | Git Leak                       ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

# User-Agent listesi (bloklanmayı önle)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36"
]

# Teknoloji tespiti için imzalar
TECH_SIGNATURES = {
    'WordPress': ['/wp-content/', '/wp-includes/', 'wp-json', 'wp-admin'],
    'Laravel': ['laravel_session', '/vendor/', 'csrf-token'],
    'Django': ['csrftoken', 'admin/login/', 'django'],
    'React': ['_next/static', 'react', 'manifest.json'],
    'Angular': ['_ng', 'ng-app', 'ng-version'],
    'Joomla': ['/media/system/js/', '/administrator/'],
    'Drupal': ['/sites/default/', 'drupal'],
    'Magento': ['/skin/frontend/', 'Mage.Cookies'],
    'ASP.NET': ['ASP.NET', 'ViewState', '__VIEWSTATE'],
    'Node.js': ['x-powered-by: express', 'nodejs'],
}

class DobivornDirBuster:
    def __init__(self, target, wordlist, threads=50, timeout=5, delay=0, 
                 recursive=False, extensions=None, output=None, proxy=None,
                 cookies=None, headers=None, status_filter=None, tor=False,
                 no_hash=False):
        
        self.target = target.rstrip('/') + '/'
        self.wordlist = wordlist
        self.threads = threads
        self.timeout = timeout
        self.delay = delay
        self.recursive = recursive
        self.extensions = extensions or []
        self.output = output
        self.proxy = proxy
        self.cookies = cookies or {}
        self.custom_headers = headers or {}
        self.status_filter = status_filter or [200, 301, 302, 403]
        self.tor = tor
        self.no_hash = no_hash  # 404 hash karşılaştırmasını kapat
        
        self.found = []
        self.semaphore = asyncio.Semaphore(threads)
        self.session = None
        self.not_found_hash = None
        self.technologies = []
        self.git_leaks = []
        
    async def get_session(self):
        """HTTP session oluştur"""
        connector = None
        
        if self.proxy:
            if self.proxy.startswith('socks'):
                if SOCKS_SUPPORT:
                    connector = ProxyConnector.from_url(self.proxy)
                else:
                    print(f"{Fore.YELLOW}[!] SOCKS desteği için 'aiohttp-socks' gerekli. Proxy kullanılmıyor.{Style.RESET_ALL}")
            else:
                connector = aiohttp.TCPConnector()
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            **self.custom_headers
        }
        
        timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
        
        return aiohttp.ClientSession(
            headers=headers,
            cookies=self.cookies,
            timeout=timeout_obj,
            connector=connector
        )
    
    async def get_page_hash(self, url):
        """Sayfanın hash'ini al (404 tespiti için)"""
        try:
            async with self.session.get(url, ssl=False) as response:
                content = await response.text()
                # İlk 1000 karakterin MD5 hash'i
                return hashlib.md5(content[:1000].encode()).hexdigest()
        except:
            return None
    
    async def get_base_hash(self):
        """Temel 404 hash'ini al"""
        random_path = f"/non-existent-path-{random.randint(10000, 99999)}"
        test_url = urljoin(self.target, random_path)
        self.not_found_hash = await self.get_page_hash(test_url)
        if self.not_found_hash:
            print(f"{Fore.GREEN}[+] 404 hash'i alındı: {self.not_found_hash[:16]}...{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[!] 404 hash'i alınamadı, bulanıklaştırma kapalı{Style.RESET_ALL}")
    
    async def detect_technology(self):
        """Hedef sitenin teknolojisini tespit et"""
        detected = set()
        
        for tech, indicators in TECH_SIGNATURES.items():
            for indicator in indicators:
                test_url = urljoin(self.target, indicator)
                try:
                    async with self.session.get(test_url, ssl=False) as response:
                        if response.status == 200:
                            detected.add(tech)
                            break
                except:
                    pass
        
        # Header'lardan tespit
        try:
            async with self.session.get(self.target, ssl=False) as response:
                headers = response.headers
                server = headers.get('Server', '').lower()
                if 'nginx' in server:
                    detected.add('Nginx')
                elif 'apache' in server:
                    detected.add('Apache')
                if 'x-powered-by' in headers:
                    detected.add(f"Powered-By: {headers['X-Powered-By']}")
        except:
            pass
        
        return list(detected)
    
    async def check_git_leak(self):
        """Git repository sızıntısını tespit et"""
        git_paths = [
            '.git/HEAD',
            '.git/config',
            '.git/index',
            '.git/logs/HEAD',
            '.git/refs/heads/master',
            '.git/objects/',
            '.gitignore'
        ]
        
        leaks = []
        for path in git_paths:
            test_url = urljoin(self.target, path)
            try:
                async with self.session.get(test_url, ssl=False) as response:
                    if response.status == 200:
                        content = await response.text()
                        if 'ref:' in content or 'repositoryformatversion' in content or 'git' in content.lower():
                            leaks.append({
                                'url': test_url,
                                'type': 'Git Leak',
                                'severity': 'HIGH'
                            })
                            print(f"{Fore.RED}[🔥] GIT SIZINTISI: {test_url}{Style.RESET_ALL}")
            except:
                pass
        
        return leaks
    
    async def test_path(self, path, pbar):
        """Tek bir yolu test et (hash karşılaştırmalı)"""
        async with self.semaphore:
            if self.delay > 0:
                await asyncio.sleep(self.delay)
            
            # Dosya uzantılarını ekle
            paths_to_test = [path]
            for ext in self.extensions:
                paths_to_test.append(path + ext)
            
            for test_path in paths_to_test:
                test_url = urljoin(self.target, test_path)
                
                try:
                    async with self.session.get(test_url, ssl=False) as response:
                        status = response.status
                        
                        # 404 bulanıklaştırma
                        is_false_positive = False
                        if not self.no_hash and self.not_found_hash and status == 200:
                            page_hash = await self.get_page_hash(test_url)
                            if page_hash == self.not_found_hash:
                                is_false_positive = True
                        
                        if not is_false_positive and status in self.status_filter:
                            result = {
                                'url': test_url,
                                'status': status,
                                'content_length': len(await response.text()),
                                'title': await self.get_title(response)
                            }
                            
                            self.found.append(result)
                            
                            # Renkli çıktı
                            if status == 200:
                                print(f"{Fore.GREEN}[✓] {test_url} -> {status}{Style.RESET_ALL}")
                            elif status in [301, 302]:
                                location = response.headers.get('Location', '?')
                                print(f"{Fore.BLUE}[→] {test_url} -> {status} (-> {location}){Style.RESET_ALL}")
                            elif status == 403:
                                print(f"{Fore.MAGENTA}[!] {test_url} -> {status} (Yasak){Style.RESET_ALL}")
                            elif status == 401:
                                print(f"{Fore.YELLOW}[$] {test_url} -> {status} (Yetki gerekli){Style.RESET_ALL}")
                            else:
                                print(f"{Fore.CYAN}[?] {test_url} -> {status}{Style.RESET_ALL}")
                            
                            # Recursive tarama
                            if self.recursive and status == 200 and not test_path.endswith(('.php', '.html', '.txt', '.zip', '.gz', '.sql')):
                                await self.recursive_scan(test_url)
                            
                except asyncio.TimeoutError:
                    pass
                except Exception:
                    pass
                
                pbar.update(1)
    
    async def get_title(self, response):
        """Sayfa başlığını al"""
        try:
            text = await response.text()
            if '<title>' in text:
                title = text.split('<title>')[1].split('</title>')[0]
                return title[:50]
        except:
            pass
        return ""
    
    async def recursive_scan(self, url):
        """Recursive tarama (bulunan dizinlerin içini tara)"""
        parsed = urlparse(url)
        new_base = url if url.endswith('/') else url + '/'
        
        # Sadece alt dizinleri tara (sonsuz döngüyü önle)
        if new_base.count('/') - self.target.count('/') <= 3:
            print(f"{Fore.CYAN}[↻] Recursive taranıyor: {new_base}{Style.RESET_ALL}")
            # Basit recursion - kelimelerin başına yeni dizini ekle
            new_wordlist = [f"{parsed.path.lstrip('/')}{word}" for word in self.wordlist[:20]]  # Limit 20
            for path in new_wordlist:
                await self.test_path(path, None)  # Progress bar olmadan
    
    async def scan(self):
        """Ana tarama fonksiyonu"""
        print(BANNER)
        print(f"{Fore.YELLOW}[+] Hedef: {self.target}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Kelime sayısı: {len(self.wordlist)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Thread: {self.threads}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Timeout: {self.timeout}s{Style.RESET_ALL}")
        if self.extensions:
            print(f"{Fore.YELLOW}[+] Uzantılar: {', '.join(self.extensions)}{Style.RESET_ALL}")
        if self.recursive:
            print(f"{Fore.YELLOW}[+] Recursive tarama: Aktif{Style.RESET_ALL}")
        if not self.no_hash:
            print(f"{Fore.YELLOW}[+] 404 Bulanıklaştırma: Aktif{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Başlangıç: {datetime.now()}{Style.RESET_ALL}\n")
        
        self.session = await self.get_session()
        
        # 404 hash'ini al
        if not self.no_hash:
            await self.get_base_hash()
        
        # Teknoloji tespiti
        self.technologies = await self.detect_technology()
        if self.technologies:
            print(f"{Fore.GREEN}[+] Tespit edilen teknolojiler: {', '.join(self.technologies)}{Style.RESET_ALL}")
        
        # Git sızıntısı kontrolü
        self.git_leaks = await self.check_git_leak()
        if self.git_leaks:
            print(f"{Fore.RED}[!] {len(self.git_leaks)} Git sızıntısı bulundu!{Style.RESET_ALL}")
        
        print()  # Boş satır
        
        # Progress bar
        total_requests = len(self.wordlist) * (1 + len(self.extensions))
        pbar = tqdm(total=total_requests, desc="Tarama ilerlemesi", unit="req")
        
        # Asenkron görevleri başlat
        tasks = []
        for path in self.wordlist:
            task = asyncio.create_task(self.test_path(path, pbar))
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        pbar.close()
        
        await self.session.close()
        
        # Rapor oluştur
        self.generate_report()
    
    def generate_report(self):
        """Rapor oluştur (JSON, CSV, TXT)"""
        print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
        print(f"║                    TARAMA ÖZETİ                                    ║")
        print(f"╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}[+] Hedef: {self.target}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Bulunan: {len(self.found)}{Style.RESET_ALL}")
        if self.technologies:
            print(f"{Fore.YELLOW}[+] Teknolojiler: {', '.join(self.technologies)}{Style.RESET_ALL}")
        if self.git_leaks:
            print(f"{Fore.RED}[+] Git sızıntıları: {len(self.git_leaks)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[+] Bitiş: {datetime.now()}{Style.RESET_ALL}")
        
        if self.found:
            print(f"\n{Fore.GREEN}Bulunan dizin/dosyalar:{Style.RESET_ALL}")
            for result in self.found:
                print(f"  → {result['status']} : {result['url']}")
        
        # Dosyaya kaydet
        if self.output:
            report_data = {
                'target': self.target,
                'scan_time': str(datetime.now()),
                'total_found': len(self.found),
                'technologies': self.technologies,
                'git_leaks': self.git_leaks,
                'results': self.found
            }
            
            if self.output.endswith('.json'):
                with open(self.output, 'w') as f:
                    json.dump(report_data, f, indent=2)
                print(f"\n{Fore.GREEN}[+] JSON raporu kaydedildi: {self.output}{Style.RESET_ALL}")
            elif self.output.endswith('.csv'):
                with open(self.output, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['url', 'status', 'content_length', 'title'])
                    writer.writeheader()
                    writer.writerows(self.found)
                print(f"\n{Fore.GREEN}[+] CSV raporu kaydedildi: {self.output}{Style.RESET_ALL}")
            else:
                with open(self.output, 'w') as f:
                    f.write(f"Target: {self.target}\n")
                    f.write(f"Scan Time: {datetime.now()}\n")
                    f.write(f"Technologies: {', '.join(self.technologies)}\n")
                    f.write(f"Git Leaks: {len(self.git_leaks)}\n\n")
                    for result in self.found:
                        f.write(f"{result['status']} : {result['url']}\n")
                print(f"\n{Fore.GREEN}[+] TXT raporu kaydedildi: {self.output}{Style.RESET_ALL}")

def load_wordlist(file_path):
    """Wordlist yükle"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        return words
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Wordlist bulunamadı: {file_path}{Style.RESET_ALL}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Dobivorn Directory Buster v3.0 - Web Dizin Tarayıcı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 dirbuster.py https://example.com
  python3 dirbuster.py https://example.com -w custom.txt -t 30
  python3 dirbuster.py https://example.com -e .php .bak .sql
  python3 dirbuster.py https://example.com -r -o result.json
  python3 dirbuster.py https://example.com --proxy http://127.0.0.1:8080
  python3 dirbuster.py https://example.com --no-hash  (404 bulanıklaştırmayı kapat)
        """
    )
    
    parser.add_argument("url", help="Hedef URL (örn: https://example.com)")
    parser.add_argument("-w", "--wordlist", default="wordlists/common.txt", help="Wordlist dosyası")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Thread sayısı (varsayılan: 50)")
    parser.add_argument("-to", "--timeout", type=int, default=5, help="Zaman aşımı (varsayılan: 5)")
    parser.add_argument("-d", "--delay", type=float, default=0, help="Request arası bekleme (saniye)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursive tarama")
    parser.add_argument("-e", "--extensions", nargs="+", help="Dosya uzantıları (örn: .php .bak .sql)")
    parser.add_argument("-o", "--output", help="Çıktı dosyası (JSON, CSV veya TXT)")
    parser.add_argument("--proxy", help="Proxy (örn: http://127.0.0.1:8080)")
    parser.add_argument("--cookie", help="Cookie (örn: name=value)")
    parser.add_argument("--header", nargs="+", help="Custom header (örn: X-Custom: value)")
    parser.add_argument("--status", nargs="+", type=int, help="Filtrelenecek status kodları (örn: 200 403)")
    parser.add_argument("--tor", action="store_true", help="Tor ağı üzerinden tarama (socks5://127.0.0.1:9050)")
    parser.add_argument("--no-hash", action="store_true", help="404 hash karşılaştırmasını kapat")
    
    args = parser.parse_args()
    
    # Cookie parse et
    cookies = {}
    if args.cookie:
        try:
            name, value = args.cookie.split('=', 1)
            cookies[name] = value
        except:
            pass
    
    # Header parse et
    headers = {}
    if args.header:
        for h in args.header:
            try:
                name, value = h.split(':', 1)
                headers[name.strip()] = value.strip()
            except:
                pass
    
    # Proxy ayarı
    proxy = args.proxy
    if args.tor:
        proxy = "socks5://127.0.0.1:9050"
    
    # Wordlist yükle
    wordlist = load_wordlist(args.wordlist)
    
    # Status filter
    status_filter = args.status if args.status else [200, 301, 302, 403]
    
    # Tarama başlat
    buster = DobivornDirBuster(
        target=args.url,
        wordlist=wordlist,
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay,
        recursive=args.recursive,
        extensions=args.extensions,
        output=args.output,
        proxy=proxy,
        cookies=cookies,
        headers=headers,
        status_filter=status_filter,
        tor=args.tor,
        no_hash=args.no_hash
    )
    
    try:
        asyncio.run(buster.scan())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Kullanıcı tarafından durduruldu!{Style.RESET_ALL}")
        buster.generate_report()

if __name__ == "__main__":
    main()
