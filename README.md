# Dobivorn Directory Buster v5.0

Yetkili guvenlik testleri icin asenkron, hizli ve rapor-odakli dizin/dosya tarayici.

## v5.0 ile gelenler

- Iki dahili wordlist profili:
  - `quick`: hizli, yuksek sinyalli tarama
  - `full`: genis kapsamli tarama
- Varsayilan tarama profili artik `quick`
- `--profile` ve `-w/--wordlist` birlikte daha esnek kullanim
- Arac cikisinda aktif wordlist bilgisi gosterimi

## Kurulum

```bash
git clone https://github.com/DobivornSec/dobivorn-dirbuster.git
cd dobivorn-dirbuster
python3 -m pip install -r requirements.txt
```

## Hizli kullanim

```bash
python3 dirbuster.py https://example.com
```

Bu komut varsayilan olarak `quick` profilini kullanir.

## Wordlist profilleri

- `wordlists/quick.txt` -> hizli pentest ilk gecis listesi
- `wordlists/full.txt` -> daha derin ve kapsamli tarama listesi
- `wordlists/common.txt` -> genis liste (geriye donuk uyumluluk)

## Ornek komutlar

### Hizli profil (onerilen ilk adim)

```bash
python3 dirbuster.py https://example.com --profile quick
```

### Genis profil

```bash
python3 dirbuster.py https://example.com --profile full -r --max-depth 2
```

### Ozel wordlist (profili override eder)

```bash
python3 dirbuster.py https://example.com -w my-custom-wordlist.txt
```

### Cikti raporu

```bash
python3 dirbuster.py https://example.com --profile full -o reports/scan.json
```

## Parametreler

| Parametre | Aciklama | Varsayilan |
|---|---|---|
| `url` | Hedef URL | Zorunlu |
| `--profile` | Dahili wordlist profili (`quick`/`full`) | `quick` |
| `-w, --wordlist` | Ozel wordlist dosyasi (profili override eder) | Yok |
| `-t, --threads` | Eszamanli istek sayisi | `50` |
| `-to, --timeout` | Timeout (saniye) | `8` |
| `-d, --delay` | Istekler arasi bekleme | `0` |
| `-r, --recursive` | Recursive tarama ac | Kapali |
| `--max-depth` | Maksimum recursive derinlik | `1` |
| `-e, --extensions` | Test edilecek uzantilar | `['', '.php', '.bak', '.old']` |
| `--retries` | Timeout/connection retry sayisi | `1` |
| `--method` | HTTP metodu (`GET`/`HEAD`) | `GET` |
| `--status` | Kabul edilen status kodlari | `200 204 301 302 307 401 403` |
| `-o, --output` | Cikti dosya yolu | Yok |
| `--output-format` | Cikti tipi (`json`,`csv`,`txt`) | uzantidan otomatik |
| `--proxy` | HTTP proxy | Yok |
| `--tor` | Tor uzerinden tarama | Kapali |
| `--cookie` | Cookie string | Yok |
| `--header` | Ozel header listesi | Yok |
| `--no-hash` | 404 fingerprint kapat | Kapali |
| `-v, --verbose` | Ayrintili hata logu | Kapali |

## Rapor formatlari

- **JSON**: tum metadata + sonuc detaylari
- **CSV**: `url,status,content_length,title,depth`
- **TXT**: hizli okunabilir ozet

## Etik kullanim

Bu arac yalnizca **izinli** ve **yetkili** guvenlik testleri icindir. Izinsiz tarama yasal sorumluluk dogurabilir.

## Lisans

MIT (`LICENSE`)
