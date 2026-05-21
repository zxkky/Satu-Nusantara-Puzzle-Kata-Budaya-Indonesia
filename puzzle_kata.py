import pygame
import random
import json
import os
import time
import hashlib
import tkinter
from tkinter import filedialog
import shutil
import sys

# ------------------------- Inisialisasi Pygame dan Tkinter -------------------------
pygame.init()   
tk_root = tkinter.Tk()
tk_root.withdraw()

# ------------------------- Konfigurasi -------------------------
# WIDTH, HEIGHT = 800, 600
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT))
FPS = 60
ROUND_TIME = 45  # detik per ronde
START_LIVES = 3
SCORE_CORRECT = 100
SCORE_WRONG_PENALTY = 10
HIGHSCORE_FILE = "scores.json"
USER_FILE = "users.json"
WORDS_FILE = "words.txt"

WORDS = []
GAME_MODES = ["tebak_gambar"]

# ------------------------- Variabel Global untuk Latar Belakang dan Suara -------------------------
BACKGROUND = {
    'login': None,
    'game': None,
    'menu': None,  # Kita bisa gunakan latar belakang game untuk menu utama atau buat yang baru
    'admin': None  # Gunakan latar belakang login atau buat yang baru
}
SOUNDS = {
    'correct': None,
    'wrong': None
}

# ------------------------- Utility -------------------------

def ensure_dirs():
    os.makedirs("images", exist_ok=True)

def load_background():
    """Memuat gambar latar belakang untuk layar tertentu."""
    global BACKGROUND
    for key, file_path in {
        'login': "aset/20251106_210830_0000.png",
        'game': "aset/20251106_212923_0000.png",
        'menu': "aset/20251106_210830_0000.png",  # Gunakan latar belakang game untuk menu, atau buat yang baru
        'admin': "aset/admin.png"  # Gunakan latar belakang login untuk admin, atau buat yang baru
    }.items():
        if os.path.exists(file_path):
            try:
                img = pygame.image.load(file_path).convert()
                img = pygame.transform.scale(img, (WIDTH, HEIGHT))
                BACKGROUND[key] = img
                print(f"[DEBUG] Latar belakang {key} dimuat dari {file_path}")
            except pygame.error as e:
                print(f"[DEBUG] Gagal memuat latar belakang {key} ({file_path}): {e}")
                BACKGROUND[key] = None
        else:
            print(f"[DEBUG] File latar belakang {key} tidak ditemukan: {file_path}")
            BACKGROUND[key] = None

def load_sounds():
    """Memuat file suara."""
    global SOUNDS
    for key, file_path in {
        'correct': "aset/correct-choice-43861.mp3",
        'wrong': "aset/fail-144746.mp3",
        'win': "aset/winner-game-sound-404167.mp3",
        'game_over': "aset/failure-drum-sound-effect-2-7184.mp3"
    }.items():
        if os.path.exists(file_path):
            try:
                sound = pygame.mixer.Sound(file_path)
                SOUNDS[key] = sound
                print(f"[DEBUG] Suara {key} dimuat dari {file_path}")
            except pygame.error as e:
                print(f"[DEBUG] Gagal memuat suara {key} ({file_path}): {e}")
                SOUNDS[key] = None
        else:
            print(f"[DEBUG] File suara {key} tidak ditemukan: {file_path}")
            SOUNDS[key] = None

def load_highscores():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_highscores(scores):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Gagal menyimpan highscore:", e)

def add_highscore(name, score):
    scores = load_highscores()
    scores.append({"name": name, "score": score, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    scores = sorted(scores, key=lambda x: (x["score"], x["time"]), reverse=True)
    save_highscores(scores)

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def register_user(username, password):
    if not username or not password or len(username) > 15 or len(password) < 4:
        return False, "Username 1-15 huruf/angka, password min 4 karakter."
    users = load_users()
    if username in users:
        return False, "Username sudah ada!"
    if not username.isalnum():
        return False, "Username hanya boleh huruf/angka!"
    users[username] = hash_password(password)
    save_users(users)
    return True, "Berhasil daftar!"

def verify_login(username, password):
    users = load_users()
    return username in users and users[username] == hash_password(password)

def load_words_file():
    if os.path.exists(WORDS_FILE):
        try:
            with open(WORDS_FILE, "r", encoding="utf-8") as f:
                return [line.strip().lower() for line in f if line.strip().isalpha()]
        except Exception:
            return []
    return []

def draw_text(screen, text, x, y, font, center=False, color=(255,255,255)):
    surf = font.render(str(text), True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)

# ------------------------- Game Class -------------------------
class PuzzleKata:
    def __init__(self, current_user, screen, clock, fonts):
        self.screen = screen
        self.clock = clock
        self.font = fonts['font']
        self.big_font = fonts['big_font']
        self.small_font = fonts['small_font']
        self.current_user = current_user
        self.images = {}
        self.load_images()
        self.reset_game_state()
        self.hint_used = False # Tambahkan ini untuk mengatur hint
        # --- TAMBAHKAN BARIS INI ---
        self.hint_button_rect = pygame.Rect(10, HEIGHT - 60, 70, 40) # Posisi di pojok kiri bawah
        # --------------------------
        # ✅ Variabel Pause
        self.paused = False
        self.pause_menu_active = False
        self.pause_options = ["Lanjutkan", "Keluar"]
        self.selected_option = 0  # Index pilihan yang dipilih

    def pause_game(self):
        print("[DEBUG] pause_game() dipanggil!")
        self.paused = True
        self.pause_menu_active = True  # ⭐️ Tambahkan ini!
        self.selected_option = 0  # Reset pilihan ke "Lanjutkan"
        print(f"[DEBUG] paused = {self.paused}, pause_menu_active = {self.pause_menu_active}")

    def resume_game(self):
        print("[DEBUG] resume_game() dipanggil!")
        self.paused = False
        self.pause_menu_active = False  # ⭐️ Tambahkan ini!
        # Perbarui waktu mulai agar timer berjalan normal
        self.start_time = time.time() - (ROUND_TIME - self.time_left)
        print(f"[DEBUG] paused = {self.paused}, pause_menu_active = {self.pause_menu_active}")

    def load_images(self):
        ensure_dirs()
        self.images = {}
        for word in WORDS:
            path = os.path.join("images", word + ".png")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (300, 300))
                    self.images[word] = img
                except Exception as e:
                    print(f"Warning: gagal muat gambar {path}: {e}")
                    self.images[word] = None
            else:
                self.images[word] = None

    def reset_game_state(self):
        self.score = 0
        self.lives = START_LIVES
        self.level = 1
        self.game_mode = random.choice(GAME_MODES)
        self.hint_used = False # Reset hint saat game baru
        self.new_round()

    def new_round(self):
        if not WORDS:
            self.target_word = None
            self.message = "Tidak ada kata! Tambahkan lewat Admin Panel."
            self.round_completed = True
            self.revealed = []
            self.alphabet_buttons = []
            self.start_time = time.time()
            self.time_left = ROUND_TIME
            # ⭐️ Tambahkan ini: Definisikan next_rect saat round_completed
            self.next_rect = pygame.Rect(WIDTH//2 - 120, 450, 240, 60)
            return
        self.target_word = random.choice(WORDS).lower()
        # reveal underscores for letters, keep non-alpha as-is
        self.revealed = ['_' if ch.isalpha() else ch for ch in self.target_word]
        self.start_time = time.time()
        self.time_left = ROUND_TIME
        self.round_completed = False
        self.used_letters = set()
        self.generate_alphabet_buttons()
        self.message = ""
        # ⭐️ Tambahkan ini: Definisikan next_rect secara default (akan digunakan saat round_completed)

        self.next_rect = pygame.Rect(WIDTH//2 - 120, 450, 240, 60) # Ini akan ditimpa di draw(), tapi minimal sudah ada
    def generate_alphabet_buttons(self):
        self.alphabet_buttons = []
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        btn_w, btn_h = 45, 45
        cols = 13
        spacing = 8
        # Posisi Y awal: Dekat bagian bawah layar
        start_y = HEIGHT - 120
        # Hitung total lebar semua tombol dan spacing dalam satu baris
        total_width_in_row = cols * btn_w + (cols - 1) * spacing
        # Hitung posisi X awal agar satu baris tombol berada di tengah layar
        start_x = (WIDTH - total_width_in_row) // 2

        for i, ch in enumerate(letters):
            row = i // cols
            col = i % cols
            # Posisi X relatif terhadap start_x
            x = start_x + col * (btn_w + spacing)
            # Posisi Y relatif terhadap start_y
            y = start_y + row * (btn_h + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            self.alphabet_buttons.append({"rect": rect, "char": ch.lower(), "used": False})

    def update_timer(self):
        # ✅ Hentikan timer saat pause
        if self.paused:
            return
        elapsed = time.time() - self.start_time
        self.time_left = max(0, ROUND_TIME - int(elapsed))

    def handle_click(self, pos):
        if self.pause_menu_active or self.paused:
            return

        if self.round_completed:
            if hasattr(self, "next_rect") and self.next_rect.collidepoint(pos):
                self.level += 1
                self.game_mode = random.choice(GAME_MODES)
                self.new_round()
            return

        if self.round_completed:
            if hasattr(self, "next_rect") and self.next_rect.collidepoint(pos):
                self.level += 1
                self.game_mode = random.choice(GAME_MODES)
                self.new_round()
            return
        if self.hint_button_rect.collidepoint(pos):
            # Panggil fungsi use_hint yang sudah kamu punya
            self.use_hint()
            # Penting: return agar tidak memproses klik huruf setelah klik hint
            return

        for btn in self.alphabet_buttons:
            if btn["rect"].collidepoint(pos) and not btn["used"]:
                btn["used"] = True
                letter = btn["char"]
                self.used_letters.add(letter)
                self.process_letter_guess(letter)
                return
            
    def process_letter_guess(self, letter):
        if not self.target_word:
            return
        if letter in self.target_word:
            for i, ch in enumerate(self.target_word):
                if ch == letter:
                    self.revealed[i] = letter
            self.message = f"Benar! Huruf '{letter.upper()}' ada."
            if SOUNDS['correct']:
                SOUNDS['correct'].play()
            if ''.join(self.revealed) == self.target_word:
                self.score += SCORE_CORRECT
                self.message = f"Benar! +{SCORE_CORRECT} poin"
                self.round_completed = True
                if SOUNDS['win']:
                    SOUNDS['win'].play()
        else:
            self.lives -= 1
            if SOUNDS['wrong']:
                SOUNDS['wrong'].play()
            self.score = max(0, self.score - SCORE_WRONG_PENALTY)
            self.message = f"Salah! -{SCORE_WRONG_PENALTY} poin. Nyawa: {self.lives}"
            return

    def use_hint(self):
        if self.hint_used:
            self.message = "dipakai!"
            return
        if self.target_word:
            hidden_indices = [i for i, ch in enumerate(self.revealed) if ch == '_']
            if hidden_indices:
                idx = random.choice(hidden_indices)
                letter = self.target_word[idx]
                self.revealed[idx] = letter
                for btn in self.alphabet_buttons:
                    if btn["char"] == letter:
                        btn["used"] = True
                self.used_letters.add(letter)
                self.hint_used = True
                self.message = f"Hint: huruf '{letter.upper()}' terbuka"
                if ''.join(self.revealed) == self.target_word:
                    self.score += SCORE_CORRECT
                    self.message = f"Benar! +{SCORE_CORRECT} poin"
                    self.round_completed = True
                    # 🎉 Saat ronde selesai dari hint → gunakan suara WIN
                    if SOUNDS['win']:
                        SOUNDS['win'].play()
                return
        self.message = "Tidak ada huruf untuk di-hint"

    def draw(self):
        # Gambar latar belakang game
        if BACKGROUND['game']:
            self.screen.blit(BACKGROUND['game'], (0, 0))
        else:
            # Jika tidak ada gambar latar belakang, gunakan warna default
            self.screen.fill((20, 40, 60))

        # --- Menu Pause ---
        # ✅ Gambar menu pause JIKA aktif
        if self.pause_menu_active:
            # Overlay semi-transparent
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            # Kotak popup menu pause
            popup_width, popup_height = 300, 200
            popup_x = (WIDTH - popup_width) // 2
            popup_y = (HEIGHT - popup_height) // 2
            pygame.draw.rect(self.screen, (50, 50, 70), pygame.Rect(popup_x, popup_y, popup_width, popup_height), border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), pygame.Rect(popup_x, popup_y, popup_width, popup_height), 2, border_radius=10)

            # Judul Pause di dalam popup
            draw_text(self.screen, "BERHENTI", popup_x + popup_width//2, popup_y + 30, self.big_font, center=True, color=(255, 255, 255))

            # Pilihan menu di dalam popup
            y_offset = popup_y + 80
            for i, option in enumerate(self.pause_options):
                color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
                draw_text(self.screen, option, popup_x + popup_width//2, y_offset, self.font, center=True, color=color)
                y_offset += 40
            pygame.display.flip()
            return # Jangan gambar elemen game saat pause aktif

        # Info Bar (tetap tampil, tapi tidak mengganggu)
        info_bar_rect = pygame.Rect(0, 0, WIDTH, 60)
        pygame.draw.rect(self.screen, (40, 60, 80, 180), info_bar_rect)
        pygame.draw.line(self.screen, (100, 150, 200), (0, 60), (WIDTH, 60), 2)

        # Menghitung posisi teks agar merata di seluruh lebar layar
        info_texts = [
            f"Skor: {self.score}",
            f"Tingkatan: {self.level}",
            f"Nyawa: {self.lives}",
            f"Waktu: {self.time_left}s",
            # Tambahkan baris ini untuk menampilkan status hint di info bar
            f"Hint: {'Tersedia' if not self.hint_used else 'Dipakai'}"
        ]
        # Jumlah teks
        num_texts = len(info_texts)
        # Jarak antar teks
        spacing = WIDTH // (num_texts + 1)  # Membagi ruang secara merata
        for i, txt in enumerate(info_texts):
            # Posisi X dihitung agar merata
            x_pos = spacing * (i + 1)
            draw_text(self.screen, txt, x_pos, 30, self.font, center=True, color=(255, 255, 255)) # Gunakan center=True untuk memastikan teks berada di tengah titik x_pos

        # Jika belum ada kata
        if not self.target_word:
            draw_text(self.screen, "Tidak ada kata untuk dimainkan.", WIDTH//2, HEIGHT//2, self.font, center=True, color=(255,100,100))
            return

        # Mode permainan
        # draw_text(self.screen, "Mode: Tebak Gambar", WIDTH//2, 90, self.small_font, center=True, color=(200,200,100))
        draw_text(self.screen, self.message, 20, 70, self.font, center=False)

        if self.round_completed:
            # --- Tampilan Saat Benar ---
            # Pesan "Benar!" di atas (diposisikan lebih tinggi)
            # draw_text(self.screen, self.message, WIDTH//2, 80, self.font, center=True, color=(0, 255, 0))

            # Kata target besar di tengah
            display_word = self.target_word.upper()
            # Gunakan font yang lebih kecil jika diperlukan untuk menghindari tumpang tindih
            word_font = pygame.font.Font(None, 56) # Ukuran font disesuaikan
            draw_text(self.screen, display_word, WIDTH//2, 150, word_font, center=True, color=(255,255,200))

            # Gambar di bawah kata
            img = self.images.get(self.target_word)
            if img:
                # Atur posisi gambar sedikit lebih rendah
                img_rect = img.get_rect(center=(WIDTH//2, 350))
                self.screen.blit(img, img_rect)
            else:
                draw_text(self.screen, "[Gambar Tidak Tersedia]", WIDTH//2, 450, self.font, center=True, color=(255,100,100))

            answer_text = f"Jawaban: {self.target_word.upper()}"
            # Ukuran teks untuk menghitung lebar dan tinggi kotak
            text_surf = self.small_font.render(answer_text, True, (50,205,50))
            text_rect = text_surf.get_rect(center=(WIDTH//2, 540)) # Posisi sesuai dengan draw_text sebelumnya

            # Gambar kotak latar belakang
            padding = 10 # Jarak antara teks dan border kotak
            box_rect = pygame.Rect(text_rect.x - padding, text_rect.y - padding, text_rect.width + 2*padding, text_rect.height + 2*padding)
            pygame.draw.rect(self.screen, (40, 40, 60, 200), box_rect, border_radius=8) # Warna gelap dengan transparansi (alpha 200)
            pygame.draw.rect(self.screen, (200, 200, 200), box_rect, 2, border_radius=8) # Border kotak

            # Gambar teks di atas kotak
            self.screen.blit(text_surf, text_rect)

            # Tombol NEXT besar di bawah, dengan jarak yang lebih aman
            self.next_rect = pygame.Rect(WIDTH//2 - 120, 600, 240, 60) # Y position dinaikkan
            pygame.draw.rect(self.screen, (255, 215, 0), self.next_rect, border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), self.next_rect, 2, border_radius=10)
            draw_text(self.screen, "NEXT", self.next_rect.centerx, self.next_rect.centery, self.font, center=True, color=(0,0,0))
        else:
            # --- Tampilan Normal (Saat Menebak) ---
            # Kata yang terbuka
            display_word = " ".join(self.revealed).upper()
            draw_text(self.screen, display_word, WIDTH//2, 120, self.big_font, center=True, color=(255,255,200))

            # Gambar
            img = self.images.get(self.target_word)
            if img:
                self.screen.blit(img, (WIDTH//2 - 150, 170))
            else:
                draw_text(self.screen, "[Gambar Tidak Tersedia]", WIDTH//2, 300, self.font, center=True, color=(255,100,100))

            # --- Bagian Baru: Gambar Tombol Hint ---
            # Warna tombol berubah jika hint sudah dipakai
            hint_button_color = (50, 150, 50) if not self.hint_used else (100, 100, 100)
            pygame.draw.rect(self.screen, hint_button_color, self.hint_button_rect, border_radius=6)
            # Border
            pygame.draw.rect(self.screen, (200, 200, 200), self.hint_button_rect, 2, border_radius=6)
            # Teks tombol berubah jika hint sudah dipakai
            hint_text = "Hint" if not self.hint_used else "Dipakai"
            draw_text(self.screen, hint_text, self.hint_button_rect.centerx, self.hint_button_rect.centery, self.small_font, center=True, color=(255, 255, 255))
            # --------------------------

            # Huruf abjad (Sekarang di tengah bawah)
            for btn in self.alphabet_buttons:
                color = (180,180,180) if not btn["used"] else (100,100,100)
                pygame.draw.rect(self.screen, color, btn["rect"], border_radius=6)
                draw_text(self.screen, btn["char"].upper(), btn["rect"].centerx, btn["rect"].centery, self.small_font, center=True, color=(0,0,0))

        pygame.display.flip()

    def game_over(self):
        # Tambahkan suara game over
        if SOUNDS['game_over']:
            SOUNDS['game_over'].play()
        add_highscore(self.current_user, self.score)
        # Muat leaderboard
        scores = load_highscores()
        total_scores = len(scores)
        items_per_page = 5  # Kurangi jumlah item per halaman jika perlu
        total_pages = max(1, (total_scores + items_per_page - 1) // items_per_page)
        current_page = 0  # Mulai dari halaman pertama
        clock = pygame.time.Clock()

        # --- DESAIN BARU (Lebih Kecil & Rapat) ---
        # Tombol Utama (dibuat lebih kecil dan rapat)
        back_button = pygame.Rect(WIDTH//2 - 100, HEIGHT - 100, 200, 50)  # Lebih kecil
        prev_button = pygame.Rect(WIDTH//2 - 140, HEIGHT - 160, 80, 35)   # Lebih kecil
        next_button = pygame.Rect(WIDTH//2 + 60, HEIGHT - 160, 80, 35)    # Lebih kecil

        showing = True
        while showing:
            # Ambil posisi mouse saat ini
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if back_button.collidepoint(pos):
                        return "menu"
                    elif prev_button.collidepoint(pos) and current_page > 0:
                        current_page -= 1
                    elif next_button.collidepoint(pos) and current_page < total_pages - 1:
                        current_page += 1

            # Gambar latar belakang
            if BACKGROUND['game']:
                self.screen.blit(BACKGROUND['game'], (0, 0))
            else:
                self.screen.fill((30, 30, 50))

            # --- GAMBAR ELEMEN BARU (Lebih Kecil & Rapat) ---

            # Judul GAME OVER (sedikit lebih kecil)
            title_font = pygame.font.Font(None, 64) # Ukuran lebih kecil
            draw_text(self.screen, "GAME OVER", WIDTH//2, 100, title_font, center=True, color=(255, 100, 100))

            # Skor Akhir dan User (sedikit lebih kecil dan rapat)
            score_font = pygame.font.Font(None, 36) # Ukuran lebih kecil
            draw_text(self.screen, f"Skor Akhir: {self.score}", WIDTH//2, 150, score_font, center=True, color=(255, 215, 0)) # Warna Emas
            draw_text(self.screen, f"Nama: {self.current_user}", WIDTH//2, 190, self.small_font, center=True, color=(200,255,200))

            # Judul Leaderboard (sedikit lebih rapat ke bawah)
            draw_text(self.screen, "TOP SKOR HARI INI", WIDTH//2, 230, self.small_font, center=True, color=(200, 220, 255)) # Gunakan small_font

            # Daftar Skor (mengurangi jarak vertikal)
            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, total_scores)
            y_offset = 270 # Mulai lebih tinggi
            if not scores:
                draw_text(self.screen, "Belum ada skor.", WIDTH//2, y_offset, self.font, center=True, color=(150, 150, 150))
            else:
                for i in range(start_idx, end_idx):
                    item = scores[i]
                    rank = i + 1
                    # Format: "1. user — 270"
                    txt = f"{rank}. {item['name']} — {item['score']}"
                    # Warna berbeda untuk peringkat 1
                    color = (255, 215, 0) if rank == 1 else (255, 255, 255)
                    # Gunakan small_font dan jarak vertikal lebih kecil (misalnya 30)
                    draw_text(self.screen, txt, WIDTH//2, y_offset, self.small_font, center=True, color=color) # <--- small_font
                    y_offset += 30 # <--- Jarak lebih kecil

            # Indikator Halaman (sedikit lebih rapat ke daftar skor)
            page_text = f"Halaman {current_page + 1} dari {total_pages}"
            draw_text(self.screen, page_text, WIDTH//2, y_offset + 5, self.small_font, center=True, color=(200, 200, 200)) # Jarak lebih kecil

            prev_hover = prev_button.collidepoint(mouse_pos)
            # Gunakan warna berbeda jika hover
            prev_color = (120, 120, 160) if prev_hover else (100, 100, 140)
            pygame.draw.rect(self.screen, prev_color, prev_button, border_radius=6)
            draw_text(self.screen, "Prev", prev_button.centerx, prev_button.centery, self.small_font, center=True, color=(255, 255, 255))

            next_hover = next_button.collidepoint(mouse_pos)
            # Gunakan warna berbeda jika hover
            next_color = (120, 120, 160) if next_hover else (100, 100, 140)
            pygame.draw.rect(self.screen, next_color, next_button, border_radius=6)
            draw_text(self.screen, "Next", next_button.centerx, next_button.centery, self.small_font, center=True, color=(255, 255, 255))

            back_hover = back_button.collidepoint(mouse_pos)
            # Gunakan warna berbeda jika hover
            back_color = (90, 150, 220) if back_hover else (70, 130, 200) # Warna sedikit berbeda saat hover
            pygame.draw.rect(self.screen, back_color, back_button, border_radius=10) # border_radius sedikit lebih kecil
            pygame.draw.rect(self.screen, (200, 200, 200), back_button, 2, border_radius=10) # border_radius sedikit lebih kecil
            draw_text(self.screen, "Menu Utama", back_button.centerx, back_button.centery - 5, self.font, center=True, color=(0,0,0)) # Offset sedikit

            pygame.display.flip()
            clock.tick(FPS)

        return "menu"
    
    def run(self):
        # return values:
        # - "menu" : request to go back to main menu
        # - "quit" : quit app
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    # ✅ Event untuk pause/resume
                    if event.key == pygame.K_ESCAPE:
                        if not self.paused:
                            self.pause_game()
                        else:
                            self.resume_game()
                    # ✅ Event navigasi menu pause
                    elif self.pause_menu_active:
                        if event.key == pygame.K_UP:
                            self.selected_option = (self.selected_option - 1) % len(self.pause_options)
                        elif event.key == pygame.K_DOWN:
                            self.selected_option = (self.selected_option + 1) % len(self.pause_options)
                        elif event.key == pygame.K_RETURN:
                            selected = self.pause_options[self.selected_option]
                            if selected == "Lanjutkan":
                                self.resume_game()
                            elif selected == "Keluar":
                                self.pause_menu_active = False
                                return "menu" # Kembali ke menu utama

            # update timer and check lose conditions
            self.update_timer()

            # if lives reached 0 (from guesses), treat as game over
            if self.lives <= 0:
                result = self.game_over()
                if result == "menu":
                    return "menu"
                else:
                    return "quit"

            # if time ran out, also game over
            if self.time_left <= 0:
                result = self.game_over()
                if result == "menu":
                    return "menu"
                else:
                    return "quit"

            # normal drawing
            self.draw()

# ------------------------- Auth Screen -------------------------
class AuthScreen:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.mode = "login"
        self.username = ""
        self.password = ""
        self.message = ""
        self.active_field = "username"

        # Muat ikon (opsional)
        self.user_icon = None
        self.pw_icon = None
        try:
            self.user_icon = pygame.image.load("aset/user.png").convert_alpha()
            self.user_icon = pygame.transform.scale(self.user_icon, (24, 24))
        except:
            print("[DEBUG] Gagal muat user_icon.png")
        
        try:
            self.pw_icon = pygame.image.load("aset/key.png").convert_alpha()
            self.pw_icon = pygame.transform.scale(self.pw_icon, (24, 24))
        except:
            print("[DEBUG] Gagal muat lock_icon.png")

    def draw_input(self, text, rect, active=False, is_password=False, label=""):
        # Gambar label
        draw_text(self.screen, label, rect.x, rect.y - 25, self.small_font, center=False, color=(0, 0, 0))
        
        # Warna border input box
        color = (255, 215, 0) if active else (100, 100, 100) # Kuning jika aktif
        pygame.draw.rect(self.screen, (40, 40, 60, 180), rect) # Background box
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=6) # Border

        # Teks di dalam box
        if is_password:
            display_text = "*" * len(text)
        else:
            display_text = text

        if not display_text:
            placeholder = "Ketik di sini..." if active else ""
            draw_text(self.screen, placeholder, rect.x + 10, rect.y + 8, self.small_font, color=(120, 120, 120))
        else:
            draw_text(self.screen, display_text, rect.x + 10, rect.y + 8, self.small_font, color=(255, 255, 255))

        # Gambar ikon (opsional)
        if self.user_icon and not is_password:
            self.screen.blit(self.user_icon, (rect.x - 30, rect.y + 6))
        elif self.pw_icon and is_password:
            self.screen.blit(self.pw_icon, (rect.x - 30, rect.y + 6))

    def draw_button(self, text, rect, color=(70,130,180), text_color=(255,255,255), hover=False):
        if hover:
            color = tuple(min(c + 30, 255) for c in color)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (200, 200, 200), rect, 2, border_radius=8)
        draw_text(self.screen, text, rect.centerx, rect.centery, self.font, center=True, color=text_color)
        
    def run(self):
        clock = pygame.time.Clock()
        
        # Atur posisi elemen
        label_user_x = WIDTH // 2 - 150
        label_pw_x = WIDTH // 2 - 150
        input_w, input_h = 300, 40
        spacing = 10

        user_rect = pygame.Rect(label_user_x, 200, input_w, input_h)
        pw_rect = pygame.Rect(label_pw_x, 270, input_w, input_h)
        
        login_btn = pygame.Rect(WIDTH // 2 - 100, 340, 200, 50)
        toggle_btn = pygame.Rect(WIDTH // 2 - 100, 410, 200, 40)
        exit_btn = pygame.Rect(WIDTH // 2 - 100, 470, 200, 40)

        while True:
            mouse_pos = pygame.mouse.get_pos()

            # Gambar latar belakang login
            if BACKGROUND['login']:
                self.screen.blit(BACKGROUND['login'], (0, 0))
            else:
                self.screen.fill((15, 20, 35))
    
            # Judul
            draw_text(self.screen, "SATU", WIDTH // 2, 100, pygame.font.Font(None, 64), center=True, color=(255, 255, 255))
            draw_text(self.screen, "NUSANTARA", WIDTH // 2, 155, pygame.font.Font(None, 64), center=True, color=(255, 255, 255))

            # Gambar input box
            self.draw_input(self.username, user_rect, self.active_field == "username", is_password=False, label="Nama:")
            self.draw_input(self.password, pw_rect, self.active_field == "password", is_password=True, label="Kata Sandi:")

            # Gambar tombol
            login_hover = login_btn.collidepoint(mouse_pos)
            self.draw_button("Masuk" if self.mode == "login" else "Daftar", login_btn, color=(0, 123, 255), hover=login_hover) # Biru untuk utama

            toggle_hover = toggle_btn.collidepoint(mouse_pos)
            self.draw_button("Ganti ke " + ("Daftar" if self.mode == "login" else "Masuk"), toggle_btn, color=(100, 100, 120), hover=toggle_hover) # Abu-abu untuk sekunder

            exit_hover = exit_btn.collidepoint(mouse_pos)
            self.draw_button("Keluar", exit_btn, color=(220, 53, 69), hover=exit_hover) # Merah untuk aksi destruktif

            # Pesan error/sukses
            if self.message:
                color = (50, 200, 50) if "berhasil" in self.message.lower() else (255, 50, 50)
                draw_text(self.screen, self.message, WIDTH // 2, 530, self.small_font, center=True, color=color)

            # Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None, "quit"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if user_rect.collidepoint(event.pos):
                        self.active_field = "username"
                    elif pw_rect.collidepoint(event.pos):
                        self.active_field = "password"
                    elif login_btn.collidepoint(event.pos):
                        if self.mode == "login":
                            if verify_login(self.username, self.password):
                                return self.username, "menu"
                            else:
                                self.message = "Login gagal! Periksa username/password."
                        else:
                            ok, msg = register_user(self.username, self.password)
                            self.message = msg
                            if ok:
                                self.mode = "login"
                                self.password = ""
                    elif toggle_btn.collidepoint(event.pos):
                        self.mode = "register" if self.mode == "login" else "login"
                        self.message = ""
                    elif exit_btn.collidepoint(event.pos):
                        return None, "quit"

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        if self.active_field == "username":
                            self.username = self.username[:-1]
                        else:
                            self.password = self.password[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.mode == "login":
                            if verify_login(self.username, self.password):
                                return self.username, "menu"
                            else:
                                self.message = "Login gagal!"
                        else:
                            ok, msg = register_user(self.username, self.password)
                            self.message = msg
                            if ok:
                                self.mode = "login"
                                self.password = ""
                    elif len((self.username if self.active_field == "username" else self.password)) < 20 and event.unicode.isprintable():
                        if self.active_field == "username":
                            self.username += event.unicode
                        else:
                            self.password += event.unicode

            pygame.display.flip()
            clock.tick(FPS)

# ------------------------- Main Menu -------------------------
class MainMenu:
    def __init__(self, screen, font, big_font, small_font, current_user):
        self.screen = screen
        self.font = font
        self.big_font = big_font
        self.small_font = small_font
        self.current_user = current_user

        # Muat ikon (opsional)
        self.play_icon = None
        self.leaderboard_icon = None
        self.logout_icon = None
        try:
            self.play_icon = pygame.image.load("aset/play.png").convert_alpha()
            self.play_icon = pygame.transform.scale(self.play_icon, (32, 32)) # Ukuran ikon lebih besar
        except:
            print("[DEBUG] Gagal muat play_icon.png")

        try:
            self.leaderboard_icon = pygame.image.load("aset/podium.png").convert_alpha()
            self.leaderboard_icon = pygame.transform.scale(self.leaderboard_icon, (32, 32)) # Ukuran ikon lebih besar
        except:
            print("[DEBUG] Gagal muat leaderboard_icon.png")

        try:
            self.logout_icon = pygame.image.load("aset/logout.png").convert_alpha()
            self.logout_icon = pygame.transform.scale(self.logout_icon, (32, 32)) # Ukuran ikon lebih besar
        except:
            print("[DEBUG] Gagal muat logout_icon.png")

    def draw_button(self, text, rect, color=(70,130,180), text_color=(255,255,255), icon=None, hover=False):
        # Jika hover, buat warna sedikit lebih terang
        if hover:
            color = tuple(min(c + 30, 255) for c in color)

        # Gambar tombol dengan border radius dan tanpa border tipis
        pygame.draw.rect(self.screen, color, rect, border_radius=15) # Border radius lebih besar

        # Tambahkan ikon jika ada
        icon_x_offset = 0
        if icon:
            # Gambar ikon di sisi kiri teks, dengan padding
            icon_x = rect.x + 30
            icon_y = rect.centery - 16  # Agar ikon berada di tengah vertikal
            self.screen.blit(icon, (icon_x, icon_y))
            icon_x_offset = 20  # Jarak antara ikon dan teks

        # Teks berada di tengah tombol secara horizontal, dengan offset jika ada ikon
        text_x = rect.centerx + icon_x_offset
        text_y = rect.centery
        # Gunakan font yang lebih besar untuk teks tombol
        button_font = pygame.font.Font(None, 36) # Atur ukuran font teks tombol
        draw_text(self.screen, text, text_x, text_y, button_font, center=True, color=text_color)

    def run(self):
        # Atur posisi dan ukuran tombol agar lebih besar dan terpusat
        btn_width = 250  # Lebar tombol lebih besar
        btn_height = 60  # Tinggi tombol lebih besar
        spacing = 40     # Jarak antar tombol

        # Hitung posisi tombol agar terpusat di tengah layar
        start_btn_y = HEIGHT // 2 - 60  # Posisi Y tombol pertama
        start_btn = pygame.Rect(WIDTH // 2 - btn_width // 2, start_btn_y, btn_width, btn_height)
        leaderboard_btn = pygame.Rect(WIDTH // 2 - btn_width // 2, start_btn_y + btn_height + spacing, btn_width, btn_height)
        logout_btn = pygame.Rect(WIDTH // 2 - btn_width // 2, start_btn_y + 2 * (btn_height + spacing), btn_width, btn_height)

        clock = pygame.time.Clock()

        while True:
            mouse_pos = pygame.mouse.get_pos()

            # Gambar latar belakang menu
            bg_key = 'menu'
            if BACKGROUND[bg_key]:
                self.screen.blit(BACKGROUND[bg_key], (0, 0))
            else:
                self.screen.fill((20, 30, 50))

            # Judul
            draw_text(self.screen, "SATU NUSANTARA", WIDTH // 2, 100, self.big_font, center=True, color=(255, 255, 255))
            draw_text(self.screen, "Mari Mengenal Budaya Indonesia", WIDTH // 2, 160, self.big_font, center=True, color=(255, 255, 255))

            # Gambar tombol-tombol
            start_hover = start_btn.collidepoint(mouse_pos)
            self.draw_button("Mulai Game", start_btn, color=(0, 123, 255), icon=self.play_icon, hover=start_hover) # Biru untuk utama

            leaderboard_hover = leaderboard_btn.collidepoint(mouse_pos)
            self.draw_button("Peringkat", leaderboard_btn, color=(70, 150, 200), icon=self.leaderboard_icon, hover=leaderboard_hover) # Biru langit

            logout_hover = logout_btn.collidepoint(mouse_pos)
            self.draw_button("Keluar", logout_btn, color=(220, 53, 69), icon=self.logout_icon, hover=logout_hover) # Merah

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_btn.collidepoint(event.pos):
                        return "game"
                    elif leaderboard_btn.collidepoint(event.pos):
                        return "leaderboard"
                    elif logout_btn.collidepoint(event.pos):
                        return "logout"

            pygame.display.flip()
            clock.tick(FPS)

# ------------------------- Leaderboard Screen -------------------------
class LeaderboardScreen:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font

    def run(self):
        back_btn = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 50)
        prev_btn = pygame.Rect(WIDTH // 2 - 160, HEIGHT - 140, 100, 40)
        next_btn = pygame.Rect(WIDTH // 2 + 60, HEIGHT - 140, 100, 40)
        clock = pygame.time.Clock()
        scores = load_highscores()
        # Urutkan secara eksplisit dari yang paling tinggi
        scores = sorted(scores, key=lambda x: (x["score"], x["time"]), reverse=True)
        total_scores = len(scores)
        items_per_page = 5
        total_pages = max(1, (total_scores + items_per_page - 1) // items_per_page)
        current_page = 0
        running = True
        while running:
            # Ambil posisi mouse saat ini
            mouse_pos = pygame.mouse.get_pos()

            # Gambar latar belakang
            if BACKGROUND['game']:
                self.screen.blit(BACKGROUND['game'], (0, 0))
            else:
                self.screen.fill((20, 30, 50))
            # Judul
            draw_text(self.screen, "Papan Peringkat", WIDTH // 2, 80, self.font, center=True, color=(255, 215, 0))
            draw_text(self.screen, "Skor Tertinggi", WIDTH // 2, 130, self.small_font, center=True, color=(255, 255, 255))
            # Hitung indeks untuk halaman saat ini
            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, total_scores)
            # Tampilkan skor
            y_offset = 170
            if not scores:
                draw_text(self.screen, "Belum ada skor.", WIDTH // 2, y_offset, self.font, center=True, color=(150, 150, 150))
            else:
                for i in range(start_idx, end_idx):
                    item = scores[i]
                    rank = i + 1
                    # Format: "1. user — 270 (2025-11-07)"
                    date_str = item['time'].split(' ')[0]  # Ambil tanggal saja
                    score_text = f"{rank}. {item['name']} — {item['score']} ({date_str})"
                    color = (255, 215, 0) if rank == 1 else (255, 255, 255)
                    draw_text(self.screen, score_text, WIDTH // 2, y_offset, self.small_font, center=True, color=color)
                    y_offset += 35
            # Indikator halaman
            page_text = f"Halaman {current_page + 1} dari {total_pages}"
            draw_text(self.screen, page_text, WIDTH // 2, y_offset + 20, self.small_font, center=True, color=(255, 255, 255))
            # Tombol Previous (dengan hover effect)
            prev_color = (120, 120, 160) if prev_btn.collidepoint(mouse_pos) else (100, 100, 140)
            pygame.draw.rect(self.screen, prev_color, prev_btn, border_radius=6)
            # Teks tombol
            draw_text(self.screen, "Kembali", prev_btn.centerx, prev_btn.centery, self.small_font, center=True, color=(255, 255, 255))
            # Tombol Next (dengan hover effect)
            next_color = (120, 120, 160) if next_btn.collidepoint(mouse_pos) else (100, 100, 140)
            pygame.draw.rect(self.screen, next_color, next_btn, border_radius=6)
            # Teks tombol
            draw_text(self.screen, "Lanjut", next_btn.centerx, next_btn.centery, self.small_font, center=True, color=(255, 255, 255))
            # Tombol Kembali ke Menu (dengan hover effect)
            # Tentukan warna berdasarkan hover
            back_color = (120, 100, 160) if back_btn.collidepoint(mouse_pos) else (100, 80, 140) # Warna sedikit berbeda dari tombol navigasi
            pygame.draw.rect(self.screen, back_color, back_btn, border_radius=10)
            # Teks tombol
            draw_text(self.screen, "Beranda", back_btn.centerx, back_btn.centery, self.font, center=True, color=(255, 255, 255))
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if back_btn.collidepoint(pos):
                        return "menu"
                    elif prev_btn.collidepoint(pos) and current_page > 0:
                        current_page -= 1
                    elif next_btn.collidepoint(pos) and current_page < total_pages - 1:
                        current_page += 1
            pygame.display.flip()
            clock.tick(FPS)
# ------------------------- Admin Login -------------------------
class AdminLogin:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.password = ""
        self.message = ""

    def run(self):
        input_box = pygame.Rect(WIDTH // 2 - 150, 280, 300, 50)
        back_btn = pygame.Rect(WIDTH // 2 - 100, 400, 200, 45)
        clock = pygame.time.Clock()
        active = False

        while True:
            # Gambar latar belakang admin login
            bg_key = 'login' # Gunakan latar belakang login atau buat yang baru
            if BACKGROUND[bg_key]:
                self.screen.blit(BACKGROUND[bg_key], (0, 0))
            else:
                 # Jika tidak ada gambar latar belakang, gunakan warna default
                self.screen.fill((20, 30, 50))

            draw_text(self.screen, "ADMIN LOGIN", WIDTH // 2, 150, pygame.font.Font(None, 64), center=True, color=(255, 100, 100))
            draw_text(self.screen, "Password:", WIDTH // 2, 240, self.font, center=True)

            # Input box
            color = (200, 200, 200) if not active else (255, 255, 255)
            pygame.draw.rect(self.screen, (50, 50, 70, 180), input_box) # Tambahkan alpha untuk transparansi jika perlu
            pygame.draw.rect(self.screen, color, input_box, 2)
            txt_surface = self.font.render("*" * len(self.password), True, (255, 255, 255))
            self.screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))

            # Pesan error / sukses
            if self.message:
                draw_text(self.screen, self.message, WIDTH // 2, 350, self.small_font, center=True, color=(255, 50, 50))

            # Tombol "Kembali"
            pygame.draw.rect(self.screen, (100, 100, 140), back_btn, border_radius=8)
            draw_text(self.screen, "Kembali", back_btn.centerx, back_btn.centery, self.small_font, center=True, color=(255, 255, 255))

            # Event handler
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Klik input box
                    if input_box.collidepoint(event.pos):
                        active = True
                    else:
                        active = False

                    # Klik tombol kembali
                    if back_btn.collidepoint(event.pos):
                        return "menu"

                if event.type == pygame.KEYDOWN and active:
                    if event.key == pygame.K_RETURN:
                        if self.password == "admin123":
                            return "admin_panel"
                        else:
                            self.message = "Password salah!"
                            self.password = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.password = self.password[:-1]
                    elif len(self.password) < 20 and event.unicode.isprintable():
                        self.password += event.unicode

            pygame.display.flip()
            clock.tick(FPS)


# ------------------------- Admin Panel -------------------------
class AdminPanel:
    def __init__(self, screen, font, small_font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.current_words = set()
        self.input_word = ""
        self.message = ""
        self.show_list = False
        self.selected_word = ""  # Kata yang dipilih
        self.edit_mode = False   # Mode edit
        self.edit_target = ""    # Kata yang sedang diedit
        ensure_dirs()
        self.load_words()
        # Muat ikon gambar
        self.edit_icon = None
        self.delete_icon = None
        try:
            self.edit_icon = pygame.image.load("aset/edit.png").convert_alpha()
            self.edit_icon = pygame.transform.scale(self.edit_icon, (20, 20))
        except:
            print("[DEBUG] Gagal muat edit.png")
        
        try:
            self.delete_icon = pygame.image.load("aset/delete.png").convert_alpha()
            self.delete_icon = pygame.transform.scale(self.delete_icon, (20, 20))
        except:
            print("[DEBUG] Gagal muat delete.png")

    def load_words(self):
        if os.path.exists(WORDS_FILE):
            with open(WORDS_FILE, "r", encoding="utf-8") as f:
                self.current_words = {line.strip().lower() for line in f if line.strip().isalpha()}
        else:
            self.current_words = set()

    def save_words(self):
        print(f"[DEBUG] Menyimpan kata: {sorted(self.current_words)}")  # Tambahkan ini
        with open(WORDS_FILE, "w", encoding="utf-8") as f:
            for w in sorted(self.current_words):
                f.write(w + "\n")
        print(f"[DEBUG] words.txt telah disimpan.")  # Tambahkan ini

    def draw_button(self, text, rect, color=(70,130,180), text_color=(255,255,255), hover=False):
        if hover:
            color = tuple(min(c + 30, 255) for c in color)
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (200,200,200), rect, 2, border_radius=8)
        draw_text(self.screen, text, rect.centerx, rect.centery, self.font, center=True, color=text_color)

    def run(self):
        clock = pygame.time.Clock()
        # Input Box
        input_box = pygame.Rect(50, 80, 300, 40)
        btn_add = pygame.Rect(370, 80, 120, 40)
        # Tombol Utama
        btn_list = pygame.Rect(50, 140, 200, 50)
        btn_upload = pygame.Rect(50, 200, 200, 50)
        btn_save_changes = pygame.Rect(270, 140, 200, 50)  # Hanya simpan, tidak keluar
        btn_back = pygame.Rect(WIDTH - 120, 20, 100, 40)   # Keluar ke menu
        # Area Daftar Kata
        list_area = pygame.Rect(50, 260, WIDTH - 100, HEIGHT - 320)
        scroll_y = 0
        max_scroll = 0
        while True:
            # Gambar latar belakang admin panel
            bg_key = 'admin'
            if BACKGROUND[bg_key]:
                self.screen.blit(BACKGROUND[bg_key], (0, 0))
            else:
                self.screen.fill((15,25,40))
            # Judul
            draw_text(self.screen, "PANEL ADMIN", WIDTH//2, 30, pygame.font.Font(None, 56), center=True, color=(255,215,0))
            # --- Bagian Input Kata Baru ---
            pygame.draw.rect(self.screen, (40,40,60, 180), input_box)
            pygame.draw.rect(self.screen, (200,200,200), input_box, 2)
            txt = self.input_word if self.input_word else "Ketik kata baru..."
            draw_text(self.screen, txt, input_box.x + 10, input_box.y + 10, self.small_font, color=(200,200,200))
            # Tombol Tambah
            mouse_pos = pygame.mouse.get_pos()
            add_hover = btn_add.collidepoint(mouse_pos)
            self.draw_button("Tambah", btn_add, hover=add_hover)
            # --- Tombol Utama ---
            list_hover = btn_list.collidepoint(mouse_pos)
            self.draw_button("Lihat Daftar", btn_list, hover=list_hover)
            upload_hover = btn_upload.collidepoint(mouse_pos)
            self.draw_button("Upload Gambar", btn_upload, hover=upload_hover)
            save_hover = btn_save_changes.collidepoint(mouse_pos)
            self.draw_button("Simpan", btn_save_changes, hover=save_hover)
            back_hover = btn_back.collidepoint(mouse_pos)
            pygame.draw.rect(self.screen, (180,60,60) if back_hover else (140,50,50), btn_back, border_radius=6)
            draw_text(self.screen, "Keluar", btn_back.centerx, btn_back.centery, self.small_font, center=True, color=(255,255,255))
            # --- Pesan ---
            if self.message:
                color = (50,200,50) if "berhasil" in self.message.lower() else (255,50,50)
                draw_text(self.screen, self.message, WIDTH//2, 240, self.small_font, center=True, color=color)
            # --- Status Mode Edit ---
            if self.edit_mode:
                draw_text(self.screen, f"Sedang Edit: {self.edit_target}", WIDTH//2, 270, self.small_font, center=True, color=(255,255,0))
                # Tombol Batal
                cancel_rect = pygame.Rect(WIDTH//2 - 60, 300, 120, 40)
                pygame.draw.rect(self.screen, (200, 100, 100), cancel_rect, border_radius=6)
                draw_text(self.screen, "Batal", cancel_rect.centerx, cancel_rect.centery, self.small_font, center=True, color=(255,255,255))
            # --- Daftar Kata (Jika Ditampilkan) ---
            if self.show_list:
                # Panel Header
                pygame.draw.rect(self.screen, (50, 70, 90), list_area, border_radius=8)
                draw_text(self.screen, "Daftar Kata", list_area.x + 10, list_area.y + 5, self.small_font, color=(255,255,255))
                # Scroll Area
                y_offset = list_area.y + 30
                words_sorted = sorted(self.current_words)
                max_scroll = max(0, len(words_sorted) * 35 - (list_area.height - 30))
                visible_start = int(scroll_y // 35)
                visible_end = min(len(words_sorted), visible_start + (list_area.height // 35) + 1)
                # Render tiap kata
                for i in range(visible_start, visible_end):
                    word = words_sorted[i]
                    word_rect = pygame.Rect(list_area.x + 10, y_offset, list_area.width - 20, 30)
                    # Highlight jika dipilih
                    color_bg = (70, 100, 130) if word == self.selected_word else (60, 80, 100)
                    pygame.draw.rect(self.screen, color_bg, word_rect, border_radius=4)
                    # Icon status gambar
                    icon = '✅' if os.path.exists(os.path.join('images', word + '.png')) else '❌'
                    draw_text(self.screen, f"{icon} {word}", word_rect.x + 5, y_offset + 5, self.small_font, color=(255,255,255))
                    # Tombol Edit & Delete (muncul saat hover di item)
                    edit_btn_rect = pygame.Rect(word_rect.right - 60, y_offset, 25, 25)
                    delete_btn_rect = pygame.Rect(word_rect.right - 30, y_offset, 25, 25)
                    if word_rect.collidepoint(mouse_pos):
                        # Tombol Edit
                        pygame.draw.rect(self.screen, (80, 180, 80), edit_btn_rect, border_radius=4)
                        if self.edit_icon:
                            self.screen.blit(self.edit_icon, (edit_btn_rect.centerx - 10, edit_btn_rect.centery - 10))
                        # Tombol Delete
                        pygame.draw.rect(self.screen, (200, 60, 60), delete_btn_rect, border_radius=4)
                        if self.delete_icon:
                            self.screen.blit(self.delete_icon, (delete_btn_rect.centerx - 10, delete_btn_rect.centery - 10))
                    y_offset += 35
                # Scroll Bar
                if max_scroll > 0:
                    scroll_height = max(20, list_area.height * (list_area.height / (len(words_sorted)*35)))
                    scroll_pos = list_area.y + 30 + (scroll_y / max_scroll) * (list_area.height - 30 - scroll_height)
                    scroll_bar = pygame.Rect(list_area.right - 10, scroll_pos, 8, scroll_height)
                    pygame.draw.rect(self.screen, (100,100,120), scroll_bar, border_radius=4)
        # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if input_box.collidepoint(pos):
                        self.edit_mode = False
                        self.edit_target = ""
                    elif btn_add.collidepoint(pos):
                        word = self.input_word.strip().lower()
                        if not word or not word.isalpha():
                            self.message = "❌ Kata harus huruf saja!"
                        elif word in self.current_words:
                            self.message = "⚠️ Kata sudah ada!"
                        else:
                            self.current_words.add(word)
                            self.save_words()
                            self.message = f"✅ '{word}' ditambahkan!"
                            self.input_word = ""
                    elif btn_list.collidepoint(pos):
                        self.show_list = not self.show_list
                        self.selected_word = ""
                        scroll_y = 0
                    elif btn_upload.collidepoint(pos):
                        if self.selected_word:
                            try:
                                file_path = filedialog.askopenfilename(
                                    title=f"Pilih gambar PNG untuk '{self.selected_word}'",
                                    filetypes=[("PNG files", "*.png")]
                                )
                                if file_path:
                                    dest = os.path.join("images", self.selected_word + ".png")
                                    shutil.copy(file_path, dest)
                                    self.message = f"✅ Gambar untuk '{self.selected_word}' diunggah!"
                            except Exception as e:
                                self.message = f"❌ Gagal: {str(e)}"
                        else:
                            self.message = "Pilih kata dulu dari daftar."
                    elif btn_save_changes.collidepoint(pos):
                        if self.edit_mode:
                            new_word = self.input_word.strip().lower()
                            if not new_word or not new_word.isalpha():
                                self.message = "❌ Masukkan kata baru yang valid."
                                self.edit_mode = False
                                self.edit_target = ""
                                self.input_word = ""
                            elif new_word == self.edit_target:
                                self.message = "⚠️ Nama baru sama dengan yang lama."
                                self.edit_mode = False
                                self.edit_target = ""
                                self.input_word = ""
                            elif new_word in self.current_words:
                                self.message = "⚠️ Kata baru sudah ada!"
                                self.edit_mode = False
                                self.edit_target = ""
                                self.input_word = ""
                            else:
                                if self.edit_target in self.current_words:
                                    self.current_words.discard(self.edit_target)
                                    self.current_words.add(new_word)
                                    self.message = f"🔄 Memproses: '{self.edit_target}' → '{new_word}'"
                                    old_img = os.path.join("images", self.edit_target + ".png")
                                    new_img = os.path.join("images", new_word + ".png")
                                    if os.path.exists(old_img):
                                        try:
                                            os.rename(old_img, new_img)
                                            self.message = f"✅ '{self.edit_target}' diubah jadi '{new_word}' + gambar diperbarui!"
                                        except Exception as e:
                                            self.message = f"❌ Gagal rename gambar: {str(e)}Tapi kata sudah diubah."
                                    else:
                                        self.message = f"✅ '{self.edit_target}' diubah jadi '{new_word}' (tidak ada gambar)."
                                    self.save_words()
                                else:
                                    self.message = f"❌ '{self.edit_target}' tidak ditemukan di daftar!"
                                self.edit_mode = False
                                self.edit_target = ""
                                self.input_word = ""
                        else:
                            word = self.input_word.strip().lower()
                            if word and word.isalpha():
                                if word in self.current_words:
                                    self.message = "⚠️ Kata sudah ada!"
                                else:
                                    self.current_words.add(word)
                                    self.save_words()
                                    self.message = f"✅ '{word}' ditambahkan!"
                                    self.input_word = ""
                            else:
                                self.save_words()
                                self.message = "✅ Perubahan disimpan!"
                    elif btn_back.collidepoint(pos):
                        return "menu"
                    elif self.edit_mode and pygame.Rect(WIDTH//2 - 60, 300, 120, 40).collidepoint(pos):
                        self.edit_mode = False
                        self.edit_target = ""
                        self.input_word = ""
                        self.message = "Edit dibatalkan."
                    elif self.show_list and list_area.collidepoint(pos):
                        words_sorted = sorted(self.current_words)
                        max_scroll = max(0, len(words_sorted) * 35 - (list_area.height - 30))
                        visible_start = int(scroll_y // 35)
                        visible_end = min(len(words_sorted), visible_start + (list_area.height // 35) + 1)
                        clicked_item = None
                        edit_rect = None
                        delete_rect = None
                        for i in range(visible_start, visible_end):
                            word = words_sorted[i]
                            y_offset = list_area.y + 30 + (i - visible_start) * 35
                            word_rect = pygame.Rect(list_area.x + 10, y_offset, list_area.width - 20, 30)
                            if word_rect.collidepoint(pos):
                                clicked_item = word
                            edit_rect = pygame.Rect(word_rect.right - 60, y_offset, 25, 25)
                            delete_rect = pygame.Rect(word_rect.right - 30, y_offset, 25, 25)
                            if edit_rect.collidepoint(pos):
                                self.edit_mode = True
                                self.edit_target = word
                                self.input_word = word
                                self.message = f"Edit: '{word}'"
                                break
                            if delete_rect.collidepoint(pos):
                                confirm = tkinter.messagebox.askyesno("Hapus Kata", f"Yakin hapus '{word}'?")
                                if confirm:
                                    self.current_words.discard(word)
                                    img_path = os.path.join("images", word + ".png")
                                    if os.path.exists(img_path):
                                        try:
                                            os.remove(img_path)
                                            self.message = f"✅ '{word}' dan gambarnya dihapus!"
                                        except Exception as e:
                                            self.message = f"❌ Gagal hapus gambar: {str(e)}"
                                    else:
                                        self.message = f"✅ '{word}' dihapus (tidak ada gambar)."
                                    self.save_words()
                                    if self.selected_word == word:
                                        self.selected_word = ""
                                break
                        if clicked_item and not (edit_rect and edit_rect.collidepoint(pos)) and not (delete_rect and delete_rect.collidepoint(pos)):
                            self.selected_word = clicked_item
                            self.message = f"Kata '{clicked_item}' dipilih."
                    elif event.button == 4 and self.show_list:
                        scroll_y = max(0, scroll_y - 35)
                    elif event.button == 5 and self.show_list:
                        scroll_y = min(max_scroll, scroll_y + 35)
                elif event.type == pygame.KEYDOWN: # <- Hanya KEYDOWN untuk AdminPanel
                    if self.edit_mode and event.key == pygame.K_RETURN:
                        new_word = self.input_word.strip().lower()
                        print(f"[DEBUG] Edit: Mencoba mengganti '{self.edit_target}' menjadi '{new_word}'")  # Debug
                        if not new_word or not new_word.isalpha():
                            print(f"[DEBUG] Gagal: Input tidak valid (kosong atau bukan huruf): '{new_word}'")  # Debug
                            self.message = "❌ Masukkan kata baru yang valid."
                            self.edit_mode = False
                            self.edit_target = ""
                            self.input_word = ""
                        elif new_word == self.edit_target:
                            print(f"[DEBUG] Gagal: Nama baru sama dengan lama: '{new_word}'")  # Debug
                            self.message = "⚠️ Nama baru sama dengan yang lama."
                            self.edit_mode = False
                            self.edit_target = ""
                            self.input_word = ""
                        elif new_word in self.current_words:
                            print(f"[DEBUG] Gagal: Kata baru '{new_word}' sudah ada di daftar.")  # Debug
                            self.message = "⚠️ Kata baru sudah ada!"
                            self.edit_mode = False
                            self.edit_target = ""
                            self.input_word = ""
                        else:
                            print(f"[DEBUG] Semua validasi lolos. Mengganti '{self.edit_target}' dengan '{new_word}'")  # Debug
                            if self.edit_target in self.current_words:
                                self.current_words.discard(self.edit_target)
                                self.current_words.add(new_word)
                                self.message = f"🔄 Memproses: '{self.edit_target}' → '{new_word}'"
                                print(f"[DEBUG] Kata berhasil diupdate di set: {self.current_words}")  # Debug
                                old_img = os.path.join("images", self.edit_target + ".png")
                                new_img = os.path.join("images", new_word + ".png")
                                print(f"[DEBUG] Mencoba rename: {old_img} -> {new_img}")  # Debug
                                if os.path.exists(old_img):
                                    try:
                                        os.rename(old_img, new_img)
                                        self.message = f"✅ '{self.edit_target}' diubah jadi '{new_word}' + gambar diperbarui!"
                                        print(f"[DEBUG] Gambar berhasil direname.")  # Debug
                                    except Exception as e:
                                        self.message = f"❌ Gagal rename gambar: {str(e)} Tapi kata sudah diubah."
                                        print(f"[DEBUG] Gagal rename gambar: {e}")  # Debug
                                else:
                                    self.message = f"✅ '{self.edit_target}' diubah jadi '{new_word}' (tidak ada gambar)."
                                    print(f"[DEBUG] Tidak ada gambar untuk direname.")  # Debug
                                self.save_words()
                            else:
                                self.message = f"❌ '{self.edit_target}' tidak ditemukan di daftar!"
                                print(f"[DEBUG] Kata lama tidak ditemukan di daftar saat rename.")  # Debug
                            self.edit_mode = False
                            self.edit_target = ""
                            self.input_word = ""
                    elif event.key == pygame.K_ESCAPE:
                        if self.edit_mode:
                            self.edit_mode = False
                            self.edit_target = ""
                            self.input_word = ""
                            self.message = "Edit dibatalkan."
                    elif self.edit_mode and event.key == pygame.K_BACKSPACE:
                        self.input_word = self.input_word[:-1]
                    elif self.edit_mode and len(self.input_word) < 20 and event.unicode.isprintable():
                        self.input_word += event.unicode
                    elif not self.edit_mode and event.key == pygame.K_BACKSPACE:
                        self.input_word = self.input_word[:-1]
                    elif not self.edit_mode and len(self.input_word) < 20 and event.unicode.isprintable():
                        self.input_word += event.unicode
            pygame.display.flip()
            clock.tick(FPS)

# ------------------------- Main Program -------------------------
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Puzzle Kata & Gambar")
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 28)
    fonts = {'font': font, 'big_font': big_font, 'small_font': small_font}

    ensure_dirs()
    load_background()
    load_sounds()

    loaded = load_words_file()
    if loaded:
        WORDS[:] = loaded
    else:
        WORDS[:] = ["apel", "buku", "meja", "kursi", "pohon"]

    current_user = None
    while True:
        if current_user is None:
            auth = AuthScreen(screen, font, small_font)
            user, state = auth.run()
            if state == "quit" or user is None:
                break
            current_user = user

            # ⭐️ Tambahkan kondisi ini: Jika user adalah admin, langsung ke AdminPanel
            if current_user.lower() == "admin":
                print(f"[DEBUG] User '{current_user}' adalah admin. Langsung ke Admin Panel setelah login.")
                panel = AdminPanel(screen, font, small_font)
                panel.run()  # Tunggu hingga panel selesai
                current_user = None  # Kembali ke login setelah keluar dari panel
                continue  # Kembali ke loop utama (login)

            continue  # Jika bukan admin, lanjutkan ke menu utama
        menu = MainMenu(screen, font, big_font, small_font, current_user)
        result = menu.run()

        if result == "game":
            WORDS[:] = load_words_file() or WORDS
            game = PuzzleKata(current_user, screen, pygame.time.Clock(), fonts)
            game_result = game.run()
            if game_result == "menu":
                continue
            elif game_result == "quit":
                break
            else:
                continue

        elif result == "admin_login":
            if current_user == "admin":
                # ⭐️ Langsung ke Admin Panel tanpa login lagi
                print(f"[DEBUG] User '{current_user}' adalah admin. Langsung ke Admin Panel.")
                panel = AdminPanel(screen, font, small_font)
                panel.run()
            else:
                # Jika bukan admin, tampilkan pesan (opsional)
                # Atau biarkan kosong
                pass
        elif result == "leaderboard":
            leaderboard = LeaderboardScreen(screen, font, small_font)
            res = leaderboard.run()
            if res == "menu":
                continue
            elif res == "quit":
                break

        elif result == "logout":
            current_user = None
            continue

        elif result == "quit":
            break

    pygame.quit()

if __name__ == "__main__":
    main()
