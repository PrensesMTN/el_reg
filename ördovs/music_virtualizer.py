"""
import pygame
import numpy as np
import librosa

# 1. Müziği yükle ve analiz et
# Librosa müziğin ses dalgalarını (y) ve örnekleme hızını (sr) çıkarır
print("Müzik dosyası analiz ediliyor, lütfen bekleyin...")
audio_path = "psyducks.mp3"  # Kendi mp3 dosyanızın adını yazın
y, sr = librosa.load(audio_path, sr=None)

# Anlık ses şiddetini (RMS) hesapla
rms = librosa.feature.rms(y=y)[0]
# Ses şiddetini 0 ile 255 arasına sığacak şekilde normalize et (ölçeklendir)
max_rms = np.max(rms) if np.max(rms) > 0 else 1
normalized_volume = (rms / max_rms) * 255

# 2. Pygame ve Pencere Kurulumu
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Müzik Ritmi ile Renk Değiştirici")

# Müziği oynatmayı başlat
pygame.mixer.music.load(audio_path)
pygame.mixer.music.play()

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Şarkının o an kaçıncı milisaniyede olduğunu al
    current_time_ms = pygame.mixer.music.get_pos()
    
    if current_time_ms != -1:  # Müzik oynatılıyorsa
        # Milisaniyeyi Librosa'nın analiz indeksine dönüştür
        current_frame = int((current_time_ms / 1000.0) * sr / 512)
        
        # İndis sınırları dışına çıkmamak için kontrol et
        if current_frame < len(normalized_volume):
            vol = normalized_volume[current_frame]
            
            # Ses şiddetine göre renkleri ayarla
            # Ses yükseldikçe Kırmızı ve Mavi renkler parlayacak
            r = int(min(vol * 1.2, 255))
            g = int(min(vol * 0.3, 255))  # Yeşil az değişsin
            b = int(min(vol * 1.1, 255))
            
            screen.fill((r, g, b))
        else:
            running = False  # Şarkı bittiyse kapat
            
    pygame.display.flip()
    clock.tick(30)  # Saniyede 30 kare yenile (akıcı olması için)

pygame.quit()

"""
"""
import pygame
import numpy as np
import librosa

# 1. Müziği yükle ve analiz et
print("Müzik dosyası analiz ediliyor, lütfen bekleyin...")
audio_path = "psyducks.mp3"  # Kendi mp3 dosyanızın adını yazın

# mono=True ve sr=None ile müziği olduğu gibi tek kanallı yüklüyoruz
y, sr = librosa.load(audio_path, sr=None, mono=True)

# Uyarıyı engellemek için parametreyi 'y' üzerinden hesaplıyoruz
song_duration = librosa.get_duration(y=y, sr=sr)

# Anlık ses şiddetini (RMS) hesapla
rms_matrix = librosa.feature.rms(y=y)

# [KRİTİK ÇÖZÜM]: Librosa'nın ürettiği iki boyutlu matrisi (array'i) 
# tek boyutlu düz bir sayı listesine çeviriyoruz. (.flatten() veya [0] ile)
rms_flat = rms_matrix.flatten()

max_rms = np.max(rms_flat) if np.max(rms_flat) > 0 else 1
normalized_volume = (rms_flat / max_rms) * 255

# 2. Pygame ve Pencere Kurulumu
pygame.init()
pygame.mixer.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 500, 400
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Müzik Çalar ve Görselleştirici")

# Müziği yükle
pygame.mixer.music.load(audio_path)
pygame.mixer.music.play()

# Kontrol Değişkenleri
is_paused = False
current_pos_seconds = 0.0  
start_ticks = pygame.time.get_ticks()  

clock = pygame.time.Clock()
running = True

# Tasarım Ölçüleri
BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 340, 50, 40)
BAR_RECT = pygame.Rect(50, 310, SCREEN_WIDTH - 100, 10)

def draw_player_ui(screen, progress, is_paused):
    "Oynatıcı arayüzünü (buton ve çubuğu) çizen fonksiyon"
    # İlerleme Çubuğu Arka Planı (Gri)
    pygame.draw.rect(screen, (80, 80, 80), BAR_RECT, border_radius=5)
    
    # Dolu İlerleme Çubuğu (Beyaz)
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(screen, (255, 255, 255), filled_bar, border_radius=5)
        
        # Çubuğun ucundaki küçük yuvarlak buton
        pygame.draw.circle(screen, (255, 255, 255), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 7)

    # Oynat / Durdur Butonu Çizimi
    pygame.draw.rect(screen, (50, 50, 50), BUTTON_RECT, border_radius=5)
    if is_paused:
        # Oynat İkonu (Üçgen)
        pt1 = (BUTTON_RECT.x + 18, BUTTON_RECT.y + 10)
        pt2 = (BUTTON_RECT.x + 18, BUTTON_RECT.y + 30)
        pt3 = (BUTTON_RECT.x + 35, BUTTON_RECT.y + 20)
        pygame.draw.polygon(screen, (255, 255, 255), [pt1, pt2, pt3])
    else:
        # Durdur İkonu (İki Dikdörtgen Çizgi)
        pygame.draw.rect(screen, (255, 255, 255), (BUTTON_RECT.x + 15, BUTTON_RECT.y + 10, 6, 20))
        pygame.draw.rect(screen, (255, 255, 255), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 10, 6, 20))

while running:
    if not is_paused:
        now = pygame.time.get_ticks()
        current_pos_seconds += (now - start_ticks) / 1000.0
        start_ticks = now
    else:
        start_ticks = pygame.time.get_ticks()

    if current_pos_seconds >= song_duration:
        running = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            # Oynat/Durdur Buton Kontrolü
            if BUTTON_RECT.collidepoint(mouse_x, mouse_y):
                if is_paused:
                    pygame.mixer.music.unpause()
                    is_paused = False
                else:
                    pygame.mixer.music.pause()
                    is_paused = True
                    
            # İlerletme / Geri Sarma Kontrolü
            elif BAR_RECT.collidepoint(mouse_x, mouse_y):
                clicked_ratio = (mouse_x - BAR_RECT.x) / BAR_RECT.width
                current_pos_seconds = clicked_ratio * song_duration
                pygame.mixer.music.play(start=current_pos_seconds)
                if is_paused:
                    pygame.mixer.music.pause()

    # --- Renk Değişimi Hesaplama ---
    current_frame = int(current_pos_seconds * sr / 512)
    
    if current_frame < len(normalized_volume):
        vol = normalized_volume[current_frame] # Artık 'vol' kesinlikle tek bir sayı!
        
        # Ritme göre dinamik renkler (Mavi ve Kırmızı ağırlıklı parlama)
        r = int(min(vol * 1.3, 255))
        g = int(min(vol * 0.4, 255))
        b = int(min(vol * 1.6, 255))
        bg_color = (r, g, b)
    else:
        bg_color = (0, 0, 0)

    # --- Çizim İşlemleri ---
    screen.fill(bg_color)
    
    progress = current_pos_seconds / song_duration
    draw_player_ui(screen, progress, is_paused)
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
"""
import pygame
import numpy as np
import librosa

# 1. Müziği yükle ve analiz et
print("Müzik dosyası analiz ediliyor, lütfen bekleyin...")
audio_path = "psyducks.mp3"  # Kendi mp3 dosyanızın adını yazın

# mono=True ile stereo sesleri tek boyuta indirgiyoruz
y, sr = librosa.load(audio_path, sr=None, mono=True)
song_duration = librosa.get_duration(y=y, sr=sr)

# Anlık ses şiddetini (RMS) hesapla ve tek boyutlu diziye çevir
rms_matrix = librosa.feature.rms(y=y)
rms_flat = rms_matrix.flatten()

max_rms = np.max(rms_flat) if np.max(rms_flat) > 0 else 1
normalized_volume = (rms_flat / max_rms) * 255

# 2. Pygame ve Pencere Kurulumu
pygame.init()
pygame.mixer.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480  # Noktaların sığması için ekranı biraz genişlettik
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ritmik Noktalar Müzik Çalar")

# Müziği yükle
pygame.mixer.music.load(audio_path)
pygame.mixer.music.play()

# Kontrol Değişkenleri
is_paused = False
current_pos_seconds = 0.0  
start_ticks = pygame.time.get_ticks()  

clock = pygame.time.Clock()
running = True

# İstediğiniz 10 Noktanın Pozisyonları
duck_positions = [
    (320, 50), (400, 150), (240, 150), (480, 250), (320, 250), 
    (160, 250), (560, 350), (400, 350), (240, 350), (80, 350)
]

# Tasarım Ölçüleri (Arayüz Alt Kısma Sabitlendi)
BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 430, 50, 35)
BAR_RECT = pygame.Rect(50, 405, SCREEN_WIDTH - 100, 10)
BACKGROUND_COLOR = (15, 15, 20)  # Sabit, loş ve şık bir arka plan

def draw_player_ui(screen, progress, is_paused):
    """Alt kısımdaki oynatıcı çubuğunu ve butonu çizer"""
    # İlerleme Çubuğu Arka Planı (Koyu Gri)
    pygame.draw.rect(screen, (60, 60, 65), BAR_RECT, border_radius=5)
    
    # Dolu İlerleme Çubuğu (Mat Beyaz)
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(screen, (200, 200, 200), filled_bar, border_radius=5)
        pygame.draw.circle(screen, (220, 220, 220), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 6)

    # Oynat / Durdur Butonu
    pygame.draw.rect(screen, (40, 40, 45), BUTTON_RECT, border_radius=5)
    if is_paused:
        pt1 = (BUTTON_RECT.x + 18, BUTTON_RECT.y + 8)
        pt2 = (BUTTON_RECT.x + 18, BUTTON_RECT.y + 27)
        pt3 = (BUTTON_RECT.x + 35, BUTTON_RECT.y + 17)
        pygame.draw.polygon(screen, (200, 200, 200), [pt1, pt2, pt3])
    else:
        pygame.draw.rect(screen, (200, 200, 200), (BUTTON_RECT.x + 16, BUTTON_RECT.y + 9, 5, 18))
        pygame.draw.rect(screen, (200, 200, 200), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 9, 5, 18))

while running:
    if not is_paused:
        now = pygame.time.get_ticks()
        current_pos_seconds += (now - start_ticks) / 1000.0
        start_ticks = now
    else:
        start_ticks = pygame.time.get_ticks()

    if current_pos_seconds >= song_duration:
        running = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            if BUTTON_RECT.collidepoint(mouse_x, mouse_y):
                if is_paused:
                    pygame.mixer.music.unpause()
                    is_paused = False
                else:
                    pygame.mixer.music.pause()
                    is_paused = True
                    
            elif BAR_RECT.collidepoint(mouse_x, mouse_y):
                clicked_ratio = (mouse_x - BAR_RECT.x) / BAR_RECT.width
                current_pos_seconds = clicked_ratio * song_duration
                pygame.mixer.music.play(start=current_pos_seconds)
                if is_paused:
                    pygame.mixer.music.pause()

    # Arka plan rengini sabit tutuyoruz
    screen.fill(BACKGROUND_COLOR)

    # --- Noktaların Ritme Göre Yanıp Sönmesi ---
    current_frame = int(current_pos_seconds * sr / 512)
    
    if current_frame < len(normalized_volume):
        vol = normalized_volume[current_frame]
    else:
        vol = 0

    # 10 Noktanın her birini farklı çarpanlarla ekrana çiziyoruz
    for i, pos in enumerate(duck_positions):
        # Her nokta için benzersiz bir renk karakteristiği atıyoruz (i değerine göre)
        # Ses sıfırken bile loş bir görünürlük için taban değer (base) ekledik (+20)
        r = int(min(20 + vol * (1.1 + (i % 3) * 0.6), 255))
        g = int(min(20 + vol * (0.2 + (i % 4) * 0.2), 250))
        b = int(min(20 + vol * (1.2 - (i % 2) * 0.5), 255))
        
        # Ritmin şiddetine göre noktaların boyutu da hafifçe büyüyüp küçülsün (Dinamik Efekt)
        radius = int(12 + (vol / 255) * 15)
        
        # Noktanın etrafına hafif bir parlama halkası ekleyelim
        pygame.draw.circle(screen, (r // 2, g // 2, b // 2), pos, radius + 4, width=2)
        # Ana noktayı çizelim
        pygame.draw.circle(screen, (r, g, b), pos, radius)

    # --- Arayüz Çizimi ---
    progress = current_pos_seconds / song_duration
    draw_player_ui(screen, progress, is_paused)
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
