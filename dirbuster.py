#!/usr/bin/env python3
"""
Dobivorn Directory Buster v5.0
High-performance web directory and file scanner for authorized assessments.
"""

import argparse
import asyncio
import csv
import hashlib
import json
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from colorama import Fore, Style, init
from tqdm import tqdm

try:
    from aiohttp_socks import ProxyConnector
    SOCKS_SUPPORT = True
except ImportError:
    ProxyConnector = None
    SOCKS_SUPPORT = False

VERSION = "5.0"
WORDLIST_PROFILES = {
    "quick": "wordlists/quick.txt",
    "full": "wordlists/full.txt",
}
DEFAULT_STATUS_FILTER = [200, 204, 301, 302, 307, 401, 403]
DEFAULT_EXTENSIONS = ["", ".php", ".bak", ".old"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36",
]

init(autoreset=True)

BANNER = f"""
{Fore.CYAN}============================================================
 Dobivorn Directory Buster v{VERSION}
 Fast | Accurate | Report-Ready
============================================================{Style.RESET_ALL}
"""


@dataclass
class ScanResult:
    url: str
    status: int
    content_length: int
    title: str
    depth: int


class DobivornDirBuster:
    def __init__(
        self,
        target: str,
        wordlist: List[str],
        threads: int = 50,
        timeout: int = 8,
        delay: float = 0,
        recursive: bool = False,
        max_depth: int = 1,
        extensions: Optional[List[str]] = None,
        output: Optional[str] = None,
        output_format: Optional[str] = None,
        proxy: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        status_filter: Optional[List[int]] = None,
        retries: int = 1,
        method: str = "GET",
        no_hash: bool = False,
        verbose: bool = False,
    ):
        self.target = target.rstrip("/") + "/"
        self.wordlist = wordlist
        self.threads = max(1, threads)
        self.timeout = timeout
        self.delay = max(0, delay)
        self.recursive = recursive
        self.max_depth = max(0, max_depth)
        self.extensions = self._normalize_extensions(extensions or DEFAULT_EXTENSIONS)
        self.output = output
        self.output_format = output_format
        self.proxy = proxy
        self.cookies = cookies or {}
        self.custom_headers = headers or {}
        self.status_filter = sorted(set(status_filter or DEFAULT_STATUS_FILTER))
        self.retries = max(0, retries)
        self.method = method.upper()
        self.no_hash = no_hash
        self.verbose = verbose

        self.semaphore = asyncio.Semaphore(self.threads)
        self.session: Optional[aiohttp.ClientSession] = None

        self.found: List[ScanResult] = []
        self.technologies: List[str] = []
        self.git_leaks: List[Dict[str, str]] = []
        self.visited_dirs: Set[str] = set()
        self.seen_urls: Set[str] = set()

        self.not_found_fingerprints: Set[Tuple[int, str]] = set()
        self.start_ts = time.perf_counter()

    @staticmethod
    def _normalize_extensions(extensions: List[str]) -> List[str]:
        normalized = []
        for ext in extensions:
            if not ext:
                normalized.append("")
                continue
            ext = ext.strip()
            if not ext:
                continue
            normalized.append(ext if ext.startswith(".") else f".{ext}")
        return sorted(set(normalized), key=lambda value: (value != "", value))

    async def get_session(self) -> aiohttp.ClientSession:
        connector = aiohttp.TCPConnector(limit=self.threads, ssl=False)
        if self.proxy and self.proxy.startswith("socks"):
            if SOCKS_SUPPORT:
                connector = ProxyConnector.from_url(self.proxy)
            else:
                self._warn("SOCKS proxy istendi ancak aiohttp-socks yüklü değil. Proxy atlanıyor.")

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            **self.custom_headers,
        }

        timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
        return aiohttp.ClientSession(
            headers=headers,
            cookies=self.cookies,
            timeout=timeout_obj,
            connector=connector,
        )

    async def request(self, url: str, method: Optional[str] = None) -> Optional[Tuple[int, str, Dict[str, str]]]:
        if not self.session:
            return None

        req_method = (method or self.method).upper()

        for attempt in range(self.retries + 1):
            try:
                async with self.session.request(req_method, url, proxy=self.proxy if self.proxy and not self.proxy.startswith("socks") else None) as response:
                    text = await response.text(errors="ignore")
                    return response.status, text, dict(response.headers)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if self.verbose:
                    self._warn(f"Istek hatasi ({attempt + 1}/{self.retries + 1}) {url}: {exc}")
                if attempt < self.retries:
                    await asyncio.sleep(min(0.75 * (attempt + 1), 2.0))
                    continue
                return None

        return None

    def _content_hash(self, text: str) -> str:
        return hashlib.md5(text[:1500].encode("utf-8", errors="ignore")).hexdigest()

    async def build_404_fingerprint(self) -> None:
        fingerprints: Set[Tuple[int, str]] = set()
        for _ in range(2):
            random_path = f"non-existent-{random.randint(10000, 99999)}"
            test_url = urljoin(self.target, random_path)
            payload = await self.request(test_url)
            if payload:
                status, body, _ = payload
                fingerprints.add((status, self._content_hash(body)))

        self.not_found_fingerprints = fingerprints
        if fingerprints:
            self._ok(f"404 fingerprint hazirlandi ({len(fingerprints)} imza)")
        else:
            self._warn("404 fingerprint alinamadi, false-positive filtre zayif kalabilir")

    async def detect_technology(self) -> List[str]:
        payload = await self.request(self.target)
        if not payload:
            return []

        status, body, headers = payload
        if status >= 500:
            return []

        body_l = body.lower()
        headers_l = {key.lower(): value.lower() for key, value in headers.items()}
        detected: Set[str] = set()

        signatures = {
            "WordPress": ["wp-content", "wp-json", "wp-includes"],
            "Laravel": ["laravel", "csrf-token", "x-laravel"],
            "Django": ["csrftoken", "django"],
            "React": ["react", "__next"],
            "Angular": ["ng-version", "angular"],
        }

        for tech, marks in signatures.items():
            if any(mark in body_l for mark in marks) or any(mark in str(headers_l) for mark in marks):
                detected.add(tech)

        server = headers_l.get("server", "")
        if "nginx" in server:
            detected.add("Nginx")
        if "apache" in server:
            detected.add("Apache")
        if "cloudflare" in server:
            detected.add("Cloudflare")

        return sorted(detected)

    async def check_git_leaks(self) -> List[Dict[str, str]]:
        leak_candidates = [
            ".git/HEAD",
            ".git/config",
            ".git/index",
            ".git/logs/HEAD",
            ".git/packed-refs",
        ]
        leaks = []

        for path in leak_candidates:
            url = urljoin(self.target, path)
            payload = await self.request(url)
            if not payload:
                continue
            status, body, _ = payload
            if status == 200 and ("ref:" in body or "repositoryformatversion" in body or "[core]" in body):
                leak = {"url": url, "type": "Git Leak", "severity": "HIGH"}
                leaks.append(leak)
                self._danger(f"Git sizintisi olasi: {url}")

        return leaks

    def is_false_positive(self, status: int, body: str) -> bool:
        if self.no_hash or not self.not_found_fingerprints:
            return False
        return (status, self._content_hash(body)) in self.not_found_fingerprints

    def extract_title(self, html: str) -> str:
        if "<title" not in html.lower():
            return ""
        try:
            lower_html = html.lower()
            start = lower_html.index("<title")
            gt = lower_html.index(">", start) + 1
            end = lower_html.index("</title>", gt)
            return html[gt:end].strip().replace("\n", " ")[:80]
        except ValueError:
            return ""

    async def test_candidate(self, base_url: str, candidate: str, depth: int, pbar: Optional[tqdm]) -> None:
        async with self.semaphore:
            if self.delay > 0:
                await asyncio.sleep(self.delay)

            for ext in self.extensions:
                tested_path = f"{candidate}{ext}"
                test_url = urljoin(base_url, tested_path)
                if test_url in self.seen_urls:
                    if pbar:
                        pbar.update(1)
                    continue
                self.seen_urls.add(test_url)

                payload = await self.request(test_url)
                if payload:
                    status, body, headers = payload
                    if status in self.status_filter and not self.is_false_positive(status, body):
                        result = ScanResult(
                            url=test_url,
                            status=status,
                            content_length=len(body),
                            title=self.extract_title(body),
                            depth=depth,
                        )
                        self.found.append(result)
                        self.print_result(result, headers)

                        if self.recursive and depth < self.max_depth and status in (200, 301, 302, 307):
                            await self.enqueue_recursive(result.url)

                if pbar:
                    pbar.update(1)

    def print_result(self, result: ScanResult, headers: Dict[str, str]) -> None:
        code = result.status
        if code == 200:
            self._ok(f"[{code}] {result.url}")
        elif code in (301, 302, 307):
            location = headers.get("Location", "?")
            self._info(f"[{code}] {result.url} -> {location}")
        elif code in (401, 403):
            self._warn(f"[{code}] {result.url}")
        else:
            self._info(f"[{code}] {result.url}")

    async def enqueue_recursive(self, discovered_url: str) -> None:
        parsed = urlparse(discovered_url)
        path = parsed.path
        if not path.endswith("/"):
            return

        normalized = path.lstrip("/")
        if not normalized or normalized in self.visited_dirs:
            return
        self.visited_dirs.add(normalized)

    async def run_level(self, base_path_prefix: str, depth: int) -> None:
        base_url = urljoin(self.target, base_path_prefix)
        candidates = [f"{base_path_prefix}{word.lstrip('/')}" for word in self.wordlist]
        total_requests = len(candidates) * len(self.extensions)
        pbar = tqdm(total=total_requests, desc=f"Depth {depth}", unit="req")

        tasks = [
            asyncio.create_task(self.test_candidate(base_url=self.target, candidate=candidate, depth=depth, pbar=pbar))
            for candidate in candidates
        ]
        await asyncio.gather(*tasks)
        pbar.close()

    async def scan(self) -> None:
        self._info(BANNER.rstrip())
        self._info(f"Target: {self.target}")
        self._info(f"Wordlist entries: {len(self.wordlist)}")
        self._info(f"Threads: {self.threads} | Retries: {self.retries} | Timeout: {self.timeout}s")
        self._info(f"Status filter: {', '.join(map(str, self.status_filter))}")

        self.session = await self.get_session()

        try:
            if not self.no_hash:
                await self.build_404_fingerprint()

            self.technologies = await self.detect_technology()
            if self.technologies:
                self._ok(f"Tespit edilen teknolojiler: {', '.join(self.technologies)}")

            self.git_leaks = await self.check_git_leaks()

            await self.run_level(base_path_prefix="", depth=0)

            if self.recursive:
                pending = sorted(self.visited_dirs)
                next_depth = 1
                while pending and next_depth <= self.max_depth:
                    self._info(f"Recursive depth {next_depth}: {len(pending)} dizin")
                    current = pending
                    pending = []
                    self.visited_dirs = set()
                    for prefix in current:
                        normalized_prefix = prefix if prefix.endswith("/") else f"{prefix}/"
                        await self.run_level(base_path_prefix=normalized_prefix, depth=next_depth)
                    pending = sorted(self.visited_dirs)
                    next_depth += 1

        finally:
            if self.session:
                await self.session.close()

        self.generate_report()

    def generate_report(self) -> None:
        end_ts = time.perf_counter()
        elapsed = round(end_ts - self.start_ts, 2)

        self._info("=" * 60)
        self._info("SCAN SUMMARY")
        self._info(f"Target: {self.target}")
        self._info(f"Findings: {len(self.found)} | Git leaks: {len(self.git_leaks)}")
        self._info(f"Duration: {elapsed}s")
        self._info("=" * 60)

        data = {
            "version": VERSION,
            "target": self.target,
            "scan_started_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": elapsed,
            "threads": self.threads,
            "timeout": self.timeout,
            "retries": self.retries,
            "recursive": self.recursive,
            "max_depth": self.max_depth,
            "status_filter": self.status_filter,
            "technologies": self.technologies,
            "git_leaks": self.git_leaks,
            "results": [asdict(item) for item in self.found],
        }

        if not self.output:
            return

        output_path = Path(self.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        fmt = (self.output_format or output_path.suffix.lstrip(".") or "json").lower()
        if fmt == "json":
            output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        elif fmt == "csv":
            with output_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["url", "status", "content_length", "title", "depth"])
                writer.writeheader()
                writer.writerows([asdict(item) for item in self.found])
        else:
            lines = [
                f"Dobivorn DirBuster v{VERSION}",
                f"Target: {self.target}",
                f"Duration: {elapsed}s",
                f"Findings: {len(self.found)}",
                f"Technologies: {', '.join(self.technologies) if self.technologies else '-'}",
                f"Git leaks: {len(self.git_leaks)}",
                "",
            ]
            for item in self.found:
                lines.append(f"[{item.status}] {item.url} (len={item.content_length}, depth={item.depth})")
            output_path.write_text("\n".join(lines), encoding="utf-8")

        self._ok(f"Rapor kaydedildi: {output_path}")

    def _ok(self, msg: str) -> None:
        print(f"{Fore.GREEN}[+] {msg}{Style.RESET_ALL}")

    def _warn(self, msg: str) -> None:
        print(f"{Fore.YELLOW}[!] {msg}{Style.RESET_ALL}")

    def _danger(self, msg: str) -> None:
        print(f"{Fore.RED}[-] {msg}{Style.RESET_ALL}")

    def _info(self, msg: str) -> None:
        print(f"{Fore.CYAN}[*] {msg}{Style.RESET_ALL}")


def load_wordlist(file_path: str) -> List[str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wordlist bulunamadi: {file_path}")

    words: List[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        words.append(stripped)

    if not words:
        raise ValueError("Wordlist bos olamaz")
    return words


def parse_cookie(cookie_str: Optional[str]) -> Dict[str, str]:
    if not cookie_str:
        return {}
    chunks = [chunk.strip() for chunk in cookie_str.split(";") if chunk.strip()]
    cookies: Dict[str, str] = {}
    for chunk in chunks:
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def parse_headers(header_list: Optional[List[str]]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if not header_list:
        return headers

    for raw in header_list:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        headers[key.strip()] = value.strip()
    return headers


def validate_target(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL gecersiz. Ornek: https://example.com")
    return url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Dobivorn Directory Buster v{VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 dirbuster.py https://example.com
  python3 dirbuster.py https://example.com --profile quick -t 100 --retries 2
  python3 dirbuster.py https://example.com --profile full -r --max-depth 2
  python3 dirbuster.py https://example.com -w mylist.txt
  python3 dirbuster.py https://example.com -e .php .bak .sql -o reports/scan.json
  python3 dirbuster.py https://example.com --status 200 401 403
""",
    )

    parser.add_argument("url", help="Target URL (example: https://example.com)")
    parser.add_argument(
        "--profile",
        choices=["quick", "full"],
        default="quick",
        help="Built-in wordlist profile",
    )
    parser.add_argument("-w", "--wordlist", help="Custom wordlist file path (overrides --profile)")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Concurrent request count")
    parser.add_argument("-to", "--timeout", type=int, default=8, help="Request timeout (seconds)")
    parser.add_argument("-d", "--delay", type=float, default=0, help="Delay between requests")
    parser.add_argument("-r", "--recursive", action="store_true", help="Enable recursive scanning")
    parser.add_argument("--max-depth", type=int, default=1, help="Maximum recursive depth")
    parser.add_argument("-e", "--extensions", nargs="+", help="File extensions (example: .php .bak .sql)")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--output-format", choices=["json", "csv", "txt"], help="Output format override")
    parser.add_argument("--proxy", help="Proxy URL (example: http://127.0.0.1:8080)")
    parser.add_argument("--cookie", help="Cookie string (example: a=1; b=2)")
    parser.add_argument("--header", nargs="+", help="Custom header list (example: Authorization: Bearer token)")
    parser.add_argument("--status", nargs="+", type=int, help="Accepted status codes")
    parser.add_argument("--tor", action="store_true", help="Use Tor proxy (socks5://127.0.0.1:9050)")
    parser.add_argument("--retries", type=int, default=1, help="Retry count on timeout/network errors")
    parser.add_argument("--method", choices=["GET", "HEAD"], default="GET", help="HTTP method")
    parser.add_argument("--no-hash", action="store_true", help="Disable 404 fingerprint filtering")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose error output")

    return parser


def resolve_wordlist_path(profile: str, custom_path: Optional[str]) -> str:
    if custom_path:
        return custom_path
    return WORDLIST_PROFILES[profile]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        target = validate_target(args.url)
        selected_wordlist = resolve_wordlist_path(args.profile, args.wordlist)
        wordlist = load_wordlist(selected_wordlist)
    except (ValueError, FileNotFoundError) as exc:
        print(f"{Fore.RED}[!] {exc}{Style.RESET_ALL}")
        sys.exit(1)

    proxy = "socks5://127.0.0.1:9050" if args.tor else args.proxy

    buster = DobivornDirBuster(
        target=target,
        wordlist=wordlist,
        threads=args.threads,
        timeout=args.timeout,
        delay=args.delay,
        recursive=args.recursive,
        max_depth=args.max_depth,
        extensions=args.extensions,
        output=args.output,
        output_format=args.output_format,
        proxy=proxy,
        cookies=parse_cookie(args.cookie),
        headers=parse_headers(args.header),
        status_filter=args.status,
        retries=args.retries,
        method=args.method,
        no_hash=args.no_hash,
        verbose=args.verbose,
    )
    print(f"{Fore.CYAN}[*] Active wordlist: {selected_wordlist}{Style.RESET_ALL}")

    try:
        asyncio.run(buster.scan())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Scan interrupted by user.{Style.RESET_ALL}")
        buster.generate_report()


if __name__ == "__main__":
    main()
