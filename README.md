# 🇮🇩 Satu Nusantara — Puzzle Kata Budaya Indonesia

> Game edukasi desktop **puzzle tebak kata berbasis gambar** bertema **budaya Indonesia**, dibangun dengan Python & Pygame. Pemain menebak nama warisan budaya dari gambarnya menggunakan tombol huruf abjad — dilengkapi sistem login, leaderboard, efek suara, dan panel admin.

---

## 🎮 Cara Bermain

1. **Login** atau daftar akun baru
2. Di layar game, sebuah **gambar budaya Indonesia** ditampilkan (contoh: wayang, reog, kebaya, silat, dll.)
3. Tebak namanya dengan **mengklik tombol huruf abjad** yang tersedia di bagian bawah layar
4. Huruf yang benar akan terungkap; huruf salah mengurangi **nyawa** dan poin
5. Gunakan **Hint** (sekali per ronde) untuk membuka satu huruf secara otomatis
6. Selesaikan sebelum **timer 45 detik** habis atau nyawa mencapai nol
7. Skor tersimpan otomatis ke **leaderboard**

---

## ✨ Fitur

- 🔐 **Sistem autentikasi** — Register & login dengan password ter-hash (SHA-256)
- 🖼️ **Mode tebak gambar** — Gambar budaya Indonesia sebagai soal utama
- ⏱️ **Timer per ronde** — 45 detik untuk menebak setiap kata
- ❤️ **Sistem nyawa** — 3 nyawa, berkurang setiap tebakan salah
- 💡 **Fitur Hint** — Buka satu huruf tersembunyi (1x per ronde)
- ⏸️ **Pause / Resume** — Tekan `ESC` untuk menjeda permainan
- 🏆 **Leaderboard** — Papan peringkat skor tertinggi dengan paginasi
- 🔊 **Efek suara** — Suara benar, salah, menang, dan game over
- 🛠️ **Panel Admin** — Kelola kata dan gambar soal langsung dari dalam game
- 📦 **Build ke .exe** — Sudah dikonfigurasi dengan PyInstaller

---

## 📁 Struktur Proyek

```
satu-nusantara/
├── puzzle_kata.py          # File utama game (source code)
├── puzzle_kata.spec        # Konfigurasi build PyInstaller
├── build/
│   └── puzzle_kata/        # File hasil proses build (otomatis)
│       ├── base_library.zip
│       ├── EXE-00.toc
│       ├── PKG-00.toc
│       ├── puzzle_kata.pkg
│       ├── PYZ-00.pyz
│       ├── PYZ-00.toc
│       ├── warn-puzzle_kata.txt
│       └── xref-puzzle_kata.html
└── dist/                   # Output siap pakai / distribusi
    ├── puzzle_kata.exe     # Executable hasil build
    ├── puzzle_kata.spec    # Salinan spec di dist
    ├── words.txt           # Daftar kata soal (dibuat otomatis)
    ├── users.json          # Data akun pengguna (dibuat otomatis)
    ├── scores.json         # Data leaderboard (dibuat otomatis)
    ├── images/             # Gambar soal (.png, nama file = kata)
    │   ├── wayang.png
    │   ├── reog.png
    │   ├── kebaya.png
    │   └── ...
    └── aset/               # Aset UI (background, ikon, suara)
        ├── 20251106_210830_0000.png     # Background layar login & menu
        ├── 20251106_212923_0000.png     # Background layar game
        ├── admin.png                    # Background panel admin
        ├── correct-choice-43861.mp3     # Suara jawaban benar
        ├── fail-144746.mp3              # Suara jawaban salah
        ├── winner-game-sound-404167.mp3 # Suara menang ronde
        ├── failure-drum-sound-effect-2-7184.mp3  # Suara game over
        ├── play.png / podium.png / logout.png    # Ikon tombol menu
        ├── user.png / key.png                    # Ikon input login
        └── edit.png / delete.png                 # Ikon admin panel
```

> **Catatan:** Saat menjalankan dari source (`puzzle_kata.py`), letakkan folder `images/` dan `aset/` di direktori yang sama dengan file `.py`. Folder `build/` dan `dist/` hanya dibutuhkan untuk proses PyInstaller.

---

## 🚀 Cara Menjalankan

### Prasyarat

- Python 3.8+
- pygame
- Pillow (opsional, untuk keperluan lain)

```bash
pip install pygame
```

### Jalankan langsung

```bash
python puzzle_kata.py
```

Pastikan folder `images/` dan `aset/` ada di direktori yang sama dengan `puzzle_kata.py`.

---

## 🧩 Kata & Soal Bawaan

Game sudah dilengkapi **9 kata budaya Indonesia** beserta gambarnya:

| Kata | Kategori |
|---|---|
| Wayang | Seni Pertunjukan |
| Reog | Seni Pertunjukan |
| Silat | Seni Bela Diri |
| Kebaya | Pakaian Tradisional |
| Kolintang | Alat Musik |
| Suling | Alat Musik |
| Kawung | Motif Batik |
| Gulungan | Motif Batik |
| Wajik | Makanan Tradisional |

---

## 🛠️ Panel Admin

Login sebagai `admin` (password dikonfigurasi saat registrasi) untuk mengakses panel admin langsung dari dalam game. Admin dapat:

- **Tambah** kata soal baru
- **Edit** nama kata yang sudah ada (nama file gambar ikut diperbarui otomatis)
- **Hapus** kata beserta gambarnya
- **Upload** gambar PNG untuk kata yang dipilih
- **Lihat daftar** kata beserta status ketersediaan gambarnya (✅/❌)

---

## 🏆 Sistem Skor

| Aksi | Poin |
|---|---|
| Tebak huruf benar | — |
| Selesaikan satu kata | +100 |
| Tebak huruf salah | -10 |
| Gunakan hint | Tidak ada pengurangan |

---

## ⌨️ Kontrol

| Tombol | Fungsi |
|---|---|
| Klik huruf | Masukkan tebakan |
| `ESC` | Pause / Resume |
| `↑ / ↓` | Navigasi menu pause |
| `Enter` | Konfirmasi pilihan menu pause |

---

## 📦 Build ke Executable (.exe)

Pastikan PyInstaller sudah terinstal:

```bash
pip install pyinstaller
```

Build menggunakan file spec yang sudah tersedia:

```bash
pyinstaller puzzle_kata.spec
```

File `.exe` akan tersimpan di folder `dist/`. Folder `images/` dan `aset/` sudah dikonfigurasi untuk ikut dikemas di dalam executable.

---

## 🛠️ Teknologi

| Komponen | Keterangan |
|---|---|
| Python 3 | Bahasa pemrograman utama |
| Pygame | Engine game & rendering |
| Tkinter | Dialog file upload di admin panel |
| hashlib | Hash password pengguna (SHA-256) |
| JSON | Penyimpanan data user & skor |
| PyInstaller | Build ke `.exe` |

---

## 📄 Lisensi

Proyek ini dibuat untuk keperluan lomba / pembelajaran bertema budaya Indonesia. Bebas digunakan dan dimodifikasi.
