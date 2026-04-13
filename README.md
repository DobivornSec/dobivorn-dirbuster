# dobivorn-dirbuster
🐉 Web uygulamaları için dizin/dosya tarayıcı. Gizli yolları, admin panellerini ve yedek dosyalarını bulur.


# Dobivorn Directory Buster 🐉

Web uygulamaları için hızlı bir dizin/dosya tarayıcı. Gizli yönetici panellerini, yedek dosyalarını ve hassas dizinleri bulur.

## Özellikler

- 🔍 Wordlist tabanlı tarama
- ⚡ Çoklu thread desteği (hızlı tarama)
- 🎨 Renkli durum kodu gösterimi
- 📋 Varsayımlı wordlist (50+ yaygın yol)
- 🎯 Özel wordlist desteği
- ⏱️ Zaman aşımı ayarı

## Kurulum

    git clone https://github.com/DobivornSec/dobivorn-dirbuster.git
    cd dobivorn-dirbuster
    pip install -r requirements.txt

## Kullanım 

# Varsayılan wordlist ile tarama
    python3 dirbuster.py https://example.com

# Özel wordlist ve thread sayısı
    python3 dirbuster.py https://example.com -w custom.txt -t 20

# Zaman aşımını artır
    python3 dirbuster.py https://example.com -to 10

## Örnek Çıktı

[✓] https://github.com/login -> 200
[→] https://github.com/admin -> 301
[!] https://github.com/wp-admin -> 403

Bulunan dizin/dosyalar:
  → 200 : https://github.com/login
  → 301 : https://github.com/admin
  → 403 : https://github.com/wp-admin

## Parametreler
Parametre	Açıklama	Varsayılan
url	Hedef URL	Zorunlu
-w, --wordlist	Wordlist dosyası	wordlists/common.txt
-t, --threads	Thread sayısı	10
-to, --timeout	Zaman aşımı (saniye)	5

## Yapılacaklar

  Recursive tarama (iç içe dizinler)

  Dosya uzantısı filtreleme

  Çıktıyı dosyaya kaydetme

  Proxy desteği
