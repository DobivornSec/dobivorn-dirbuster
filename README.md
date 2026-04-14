# 🐉 Dobivorn Directory Buster v3.0

> **3 Başlı Ejderha** | Red Team | Purple Team | Blue Team

Web uygulamaları için **profesyonel** dizin/dosya tarayıcı. Gizli yolları, admin panellerini, yedek dosyalarını ve hassas dizinleri bulur.

---

## ✨ Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🔍 **Wordlist tabanlı** | 50+ yaygın yol ile hızlı tarama |
| ⚡ **Asenkron mimari** | 800+ request/saniye hız |
| 🎨 **Renkli çıktı** | Durum kodlarına göre renklendirme |
| 🔥 **404 Bulanıklaştırma** | Hash karşılaştırma ile false positive temizliği |
| 🕵️ **Teknoloji tespiti** | WordPress, Laravel, Django, React, Angular |
| 💀 **Git sızıntısı** | `.git/HEAD`, `.git/config` tespiti |
| 📁 **Recursive tarama** | Bulunan dizinlerin içini de tara |
| 🔌 **Çoklu uzantı** | `.php .bak .sql .tar.gz .zip` desteği |
| 📊 **Raporlama** | JSON, CSV, TXT formatlarında çıktı |
| 🕵️ **Proxy/Tor** | Anonim tarama desteği |
| 🍪 **Cookie/Header** | Auth gerektiren siteler için |

---

## 📦 Kurulum

```bash
git clone https://github.com/DobivornSec/dobivorn-dirbuster.git
cd dobivorn-dirbuster
pip install -r requirements.txt
```

---

## 🚀 Kullanım

### Temel tarama
```bash
python3 dirbuster.py https://example.com
```

### Özel wordlist ve thread sayısı
```bash
python3 dirbuster.py https://example.com -w custom.txt -t 100
```

### Çoklu uzantı ekleme
```bash
python3 dirbuster.py https://example.com -e .php .bak .sql .tar.gz
```

### Recursive tarama + JSON rapor
```bash
python3 dirbuster.py https://example.com -r -o sonuc.json
```

### Status koduna göre filtreleme
```bash
python3 dirbuster.py https://example.com --status 200 403
```

### Proxy ile (Burp Suite)
```bash
python3 dirbuster.py https://example.com --proxy http://127.0.0.1:8080
```

### Tor ile anonim tarama
```bash
python3 dirbuster.py https://example.com --tor
```

### 404 bulanıklaştırmayı kapat
```bash
python3 dirbuster.py https://example.com --no-hash
```

---

## 🔧 Parametreler

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `url` | Hedef URL | Zorunlu |
| `-w, --wordlist` | Wordlist dosyası | `wordlists/common.txt` |
| `-t, --threads` | Thread sayısı | 50 |
| `-to, --timeout` | Zaman aşımı (saniye) | 5 |
| `-d, --delay` | Request arası bekleme | 0 |
| `-r, --recursive` | Recursive tarama | Kapalı |
| `-e, --extensions` | Dosya uzantıları | Yok |
| `-o, --output` | Çıktı dosyası (JSON/CSV/TXT) | Yok |
| `--proxy` | Proxy adresi | Yok |
| `--cookie` | Cookie (name=value) | Yok |
| `--header` | Custom header | Yok |
| `--status` | Filtrelenecek status kodları | 200,301,302,403 |
| `--tor` | Tor ağı üzerinden tarama | Kapalı |
| `--no-hash` | 404 bulanıklaştırmayı kapat | Kapalı |

---

## 📊 Örnek Çıktı

```bash
╔══════════════════════════════════════════════════════════════╗
║   🐉 Dobivorn Directory Buster v3.0 - 3 Başlı Ejderha       ║
║   🔴 Red Team | 🟣 Purple Team | 🔵 Blue Team                ║
║   ✨ 404 Hash | Tech Detect | Git Leak                       ║
╚══════════════════════════════════════════════════════════════╝

[+] Hedef: https://google.com/
[+] Kelime sayısı: 49
[+] 404 Bulanıklaştırma: Aktif

[+] 404 hash'i alındı: 14c6bdc8365440bc...
[+] Tespit edilen teknolojiler: Nginx

[✓] https://google.com/robots.txt -> 200
[✓] https://google.com/sitemap.xml -> 200
[✓] https://google.com/images -> 200
[✓] https://google.com/mail -> 200

[!] https://tesla.com/admin -> 403 (Yasak)
[!] https://tesla.com/.env -> 403 (Yasak)
[🔥] GIT SIZINTISI: https://example.com/.git/HEAD

╔══════════════════════════════════════════════════════════════╗
║                    TARAMA ÖZETİ                             ║
╚══════════════════════════════════════════════════════════════╝
[+] Hedef: https://google.com/
[+] Bulunan: 4
[+] Teknolojiler: Nginx
[+] Bitiş: 2026-04-14 11:35:26
```

---

## ⚠️ Uyarı

> Bu araç **eğitim ve yetkili testler** için geliştirilmiştir. İzinsiz kullanım yasa dışıdır. Sorumluluk kullanıcıya aittir.

---

## ⭐ Star Atmayı Unutma!

Beğendiysen GitHub'da ⭐ bırakmayı unutma!
```

**Bu kadar!** 
