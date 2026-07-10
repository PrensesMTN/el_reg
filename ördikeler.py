"""
import pygame
import numpy as np
import librosa
import cv2
import mediapipe as mp
import math

# 1. Müziği yükle ve analiz et
print("Müzik dosyası analiz ediliyor, lütfen bekleyin...")
audio_path = "psyducks.mp3"  # Kendi mp3 dosyanızın adını yazın

y, sr = librosa.load(audio_path, sr=None, mono=True)
song_duration = librosa.get_duration(y=y, sr=sr)

rms_matrix = librosa.feature.rms(y=y)
rms_flat = rms_matrix.flatten()

max_rms = np.max(rms_flat) if np.max(rms_flat) > 0 else 1
normalized_volume = (rms_flat / max_rms) * 255

# 2. MediaPipe ve OpenCV Kurulumu
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

# 3. Pygame ve Pencere Kurulumu
pygame.init()
pygame.mixer.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("El Kontrollü Ritmik Noktalar")

pygame.mixer.music.load(audio_path)

# Kontrol Değişkenleri
is_paused = False
current_pos_seconds = 0.0  
start_ticks = pygame.time.get_ticks()  
clock = pygame.time.Clock()
running = True

# Mod Kontrolü: True ise Şarkı Ritmi aktif, False ise Manuel Dokunma aktif
music_visualizer_mode = False 
button_pressed_cooldown = 0  # Butona üst üste tetiklenmeyi önlemek için zamanlayıcı

# 10 Noktanın Pozisyonları
duck_positions = [
    (320, 50), (400, 150), (240, 150), (480, 250), (320, 250), 
    (160, 250), (560, 350), (400, 350), (240, 350), (80, 350)
]

# Her noktanın manuel dokunma durumundaki parlaklık takibi
manual_point_brightness = [0] * 10

# Tasarım Ölçüleri
BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 430, 50, 35)
BAR_RECT = pygame.Rect(50, 405, SCREEN_WIDTH - 100, 10)
MODE_BUTTON_RECT = pygame.Rect(480, 15, 140, 40) # Sağ üstteki mod butonu
BACKGROUND_COLOR = (15, 15, 20)

def draw_player_ui(screen, progress, is_paused, mode_active):
    "Alt arayüzü ve sağ üstteki modu çizer"
    # İlerleme Çubuğu
    pygame.draw.rect(screen, (60, 60, 65), BAR_RECT, border_radius=5)
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(screen, (200, 200, 200), filled_bar, border_radius=5)
        pygame.draw.circle(screen, (220, 220, 220), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 6)

    # Oynat / Durdur Butonu
    pygame.draw.rect(screen, (40, 40, 45), BUTTON_RECT, border_radius=5)
    if is_paused:
        pygame.draw.polygon(screen, (200, 200, 200), [(BUTTON_RECT.x + 18, BUTTON_RECT.y + 8), (BUTTON_RECT.x + 18, BUTTON_RECT.y + 27), (BUTTON_RECT.x + 35, BUTTON_RECT.y + 17)])
    else:
        pygame.draw.rect(screen, (200, 200, 200), (BUTTON_RECT.x + 16, BUTTON_RECT.y + 9, 5, 18))
        pygame.draw.rect(screen, (200, 200, 200), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 9, 5, 18))

    # Sağ Üst Mod Değiştirme Butonu Çizimi
    btn_color = (0, 180, 100) if mode_active else (180, 50, 50)
    pygame.draw.rect(screen, btn_color, MODE_BUTTON_RECT, border_radius=8)
    
    # Buton Yazısı Fontu (Font yüklenemezse varsayılan kullanır)
    font = pygame.font.SysFont("Arial", 14, bold=True)
    text_str = "RITIM MODU" if mode_active else "DOKUNMA MODU"
    text_surface = font.render(text_str, True, (255, 255, 255))
    screen.blit(text_surface, (MODE_BUTTON_RECT.x + 15, MODE_BUTTON_RECT.y + 12))

while running:
    # --- OpenCV Kamera ve MediaPipe İşlemleri ---
    success, img = cap.read()
    if not success:
        break
        
    img = cv2.flip(img, 1) # Aynalama efekti (Sağ el sağda görünsün)
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    right_index_finger = None
    left_thumb = None
    left_index = None

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_lms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Eklemleri kamerada çiz
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            hand_label = handedness.classification[0].label # "Left" ya da "Right"
            
            # İşaret parmağı (8) ve baş parmak (4) uç noktalarını al
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * SCREEN_WIDTH), int(lm.y * SCREEN_HEIGHT)
                
                if hand_label == "Right": # Sağ El
                    if id == 8: # Sağ işaret parmağı
                        right_index_finger = (cx, cy)
                
                elif hand_label == "Left": # Sol El
                    if id == 4: left_thumb = (cx, cy)
                    if id == 8: left_index = (cx, cy)

    # --- Sol El Ses Kontrolü ---
    if left_thumb and left_index:
        # İki parmak arası mesafeyi hesapla
        distance = math.hypot(left_index[0] - left_thumb[0], left_index[1] - left_thumb[1])
        # Mesafeyi 20px-150px arasından 0.0 - 1.0 ses seviyesine eşle
        volume_level = np.clip((distance - 20) / 130, 0.0, 1.0)
        pygame.mixer.music.set_volume(volume_level)
        # Kamerada aradaki çizgiyi göster
        cv2.line(img, left_thumb, left_index, (0, 255, 0), 3)

    # --- Zaman ve Müzik Akış Kontrolü ---
    if music_visualizer_mode and not is_paused:
        now = pygame.time.get_ticks()
        current_pos_seconds += (now - start_ticks) / 1000.0
        start_ticks = now
    else:
        start_ticks = pygame.time.get_ticks()

    if music_visualizer_mode and current_pos_seconds >= song_duration:
        pygame.mixer.music.stop()
        music_visualizer_mode = False
        current_pos_seconds = 0.0

    # Pygame Olay Kontrolleri (Fare ile de kontrolü bozmamak adına korundu)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if BUTTON_RECT.collidepoint(mouse_x, mouse_y):
                if is_paused: pygame.mixer.music.unpause(); is_paused = False
                else: pygame.mixer.music.pause(); is_paused = True
            elif BAR_RECT.collidepoint(mouse_x, mouse_y):
                clicked_ratio = (mouse_x - BAR_RECT.x) / BAR_RECT.width
                current_pos_seconds = clicked_ratio * song_duration
                pygame.mixer.music.play(start=current_pos_seconds)

    # --- Sağ El Buton ve Nokta Dokunma Etkileşimi ---
    if button_pressed_cooldown > 0:
        button_pressed_cooldown -= 1

    if right_index_finger:
        rx, ry = right_index_finger
        
        # Sağ üstteki Butona basıldı mı?
        if MODE_BUTTON_RECT.collidepoint(rx, ry) and button_pressed_cooldown == 0:
            music_visualizer_mode = not music_visualizer_mode
            button_pressed_cooldown = 15 # 15 karelik basma koruması
            
            if music_visualizer_mode:
                pygame.mixer.music.play(start=current_pos_seconds)
                is_paused = False
            else:
                pygame.mixer.music.stop()
                current_pos_seconds = 0.0

        # Eğer Ritim modu kapalıysa, el ile dokunulan noktaları algıla
        if not music_visualizer_mode:
            for i, pos in enumerate(duck_positions):
                dist_to_point = math.hypot(rx - pos[0], ry - pos[1])
                if dist_to_point < 25: # Noktaya 25 piksel yakınsa dokunmuş say
                    manual_point_brightness[i] = 255 # Maksimum parla
                else:
                    manual_point_brightness[i] = max(0, manual_point_brightness[i] - 15) # Yavaşça sön

    # --- Ekranı Çizme İşlemleri ---
    screen.fill(BACKGROUND_COLOR)

    current_frame = int(current_pos_seconds * sr / 512)
    vol = normalized_volume[current_frame] if (music_visualizer_mode and current_frame < len(normalized_volume)) else 0

    # 10 Noktanın Modlara Göre Çizilmesi
    for i, pos in enumerate(duck_positions):
        if music_visualizer_mode:
            # ŞARKININ RİTMİNE GÖRE RENKLENME (Önceki mantık korundu)
            r = int(min(20 + vol * (1.0 + (i % 3) * 0.3), 255))
            g = int(min(20 + vol * (0.2 + (i % 4) * 0.4), 255))
            b = int(min(20 + vol * (1.5 - (i % 2) * 0.5), 255))
            radius = int(12 + (vol / 255) * 15)
        else:
            # SADECE PARMAKLA DOKUNARAK RENKLENME
            # Dokunulduğunda her daire kendine has sabit bir renkte parlar
            bright = manual_point_brightness[i]
            r = int(bright if i % 3 == 0 else bright * 0.3)
            g = int(bright if i % 3 == 1 else bright * 0.2)
            b = int(bright if i % 3 == 2 else bright * 0.9)
            radius = 15 if bright > 0 else 12

        # Çemberleri çiz
        if r > 20 or g > 20 or b > 20: # Görünür renk varsa parlama efekti ekle
            pygame.draw.circle(screen, (r // 2, g // 2, b // 2), pos, radius + 4, width=2)
        pygame.draw.circle(screen, (max(20, r), max(20, g), max(20, b)), pos, radius)

    # Arayüz Elemanlarını Çiz
    progress = (current_pos_seconds / song_duration) if music_visualizer_mode else 0.0
    draw_player_ui(screen, progress, is_paused, music_visualizer_mode)
    
    # Görselleştirmeyi güncelle
    pygame.display.flip()
    
    # OpenCV kamerasını ekranda küçük bir pencerede göster (Hata ayıklamak ve elleri görmek için)
    cv2.imshow("Kamera Takip (MediaPipe)", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False
        
    clock.tick(30)

# Çıkış işlemleri
cap.release()
cv2.destroyAllWindows()
pygame.quit()
"""

import pygame
import numpy as np
import librosa
import cv2
import mediapipe as mp
import math

# 1. Müziği yükle ve analiz et
print("Müzik dosyası analiz ediliyor, lütfen bekleyin...")
audio_path = "psyducks.mp3"  # Kendi mp3 dosyanızın adını yazın

y, sr = librosa.load(audio_path, sr=None, mono=True)
song_duration = librosa.get_duration(y=y, sr=sr)

rms_matrix = librosa.feature.rms(y=y)
rms_flat = rms_matrix.flatten()

max_rms = np.max(rms_flat) if np.max(rms_flat) > 0 else 1
normalized_volume = (rms_flat / max_rms) * 255

# 2. MediaPipe ve OpenCV Kurulumu
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

# KAmera boyutunu Pygame ekranına sabitlemek için zorluyoruz
SCREEN_WIDTH, SCREEN_HEIGHT = 680, 480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, SCREEN_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)

# 3. Pygame ve Pencere Kurulumu
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Kameraya Gömülü Ritmik Noktalar")

pygame.mixer.music.load(audio_path)

# Kontrol Değişkenleri
is_paused = False
current_pos_seconds = 0.0  
start_ticks = pygame.time.get_ticks()  
clock = pygame.time.Clock()
running = True

music_visualizer_mode = False 
button_pressed_cooldown = 0  

# 10 Noktanın Pozisyonları
duck_positions = [
    (320, 50), (400, 150), (240, 150), (480, 250), (320, 250), 
    (160, 250), (560, 350), (400, 350), (240, 350), (80, 350)
]

manual_point_brightness = [0] * 10

# Tasarım Ölçüleri
BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 430, 50, 35)
BAR_RECT = pygame.Rect(50, 405, SCREEN_WIDTH - 100, 10)
MODE_BUTTON_RECT = pygame.Rect(480, 15, 140, 40)

# Şeffaflık (Alpha) Değeri: 0 (Tamamen Görünmez) - 255 (Tamamen Opak)
ALPHA_VAL = 100  # Hayalet efekti dereceszt (İstediğiniz gibi değiştirebilirsiniz)

def draw_player_ui(screen, progress, is_paused, mode_active):
    "Alt arayüzü ve sağ üstteki modu YARI SAYDAM olarak çizer"
    # Şeffaf çizimler için geçici yüzey oluşturuyoruz
    ui_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    # İlerleme Çubuğu Arka Planı (Şeffaf Gri)
    pygame.draw.rect(ui_surface, (60, 60, 65, ALPHA_VAL), BAR_RECT, border_radius=5)
    
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(ui_surface, (200, 200, 200, ALPHA_VAL + 40), filled_bar, border_radius=5)
        pygame.draw.circle(ui_surface, (220, 220, 220, ALPHA_VAL + 40), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 6)

    # Oynat / Durdur Butonu (Şeffaf)
    pygame.draw.rect(ui_surface, (40, 40, 45, ALPHA_VAL), BUTTON_RECT, border_radius=5)
    if is_paused:
        pygame.draw.polygon(ui_surface, (200, 200, 200, ALPHA_VAL + 50), [(BUTTON_RECT.x + 18, BUTTON_RECT.y + 8), (BUTTON_RECT.x + 18, BUTTON_RECT.y + 27), (BUTTON_RECT.x + 35, BUTTON_RECT.y + 17)])
    else:
        pygame.draw.rect(ui_surface, (200, 200, 200, ALPHA_VAL + 50), (BUTTON_RECT.x + 16, BUTTON_RECT.y + 9, 5, 18))
        pygame.draw.rect(ui_surface, (200, 200, 200, ALPHA_VAL + 50), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 9, 5, 18))

    # Sağ Üst Mod Değiştirme Butonu (Şeffaf Renkli)
    btn_color = (0, 180, 100, ALPHA_VAL + 20) if mode_active else (180, 50, 50, ALPHA_VAL + 20)
    pygame.draw.rect(ui_surface, btn_color, MODE_BUTTON_RECT, border_radius=8)
    
    # Yazıyı yüzeye ekleme
    font = pygame.font.SysFont("Arial", 14, bold=True)
    text_str = "RITIM MODU" if mode_active else "DOKUNMA MODU"
    text_surface = font.render(text_str, True, (255, 255, 255))
    
    # Şeffaf yüzeyi ana ekrana yapıştırıyoruz
    screen.blit(ui_surface, (0, 0))
    screen.blit(text_surface, (MODE_BUTTON_RECT.x + 15, MODE_BUTTON_RECT.y + 12))

while running:
    # --- OpenCV Kamera ve MediaPipe İşlemleri ---
    success, img = cap.read()
    if not success:
        break
        
    img = cv2.flip(img, 1) # Aynalama efekti
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    right_index_finger = None
    left_thumb = None
    left_index = None

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_lms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            # Eklemleri kamerada çiziyoruz
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            
            # DOĞRU KULLANIM: listenin ilk elemanından label bilgisini alıyoruz
            hand_label = handedness.classification[0].label
            
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * SCREEN_WIDTH), int(lm.y * SCREEN_HEIGHT)
                if hand_label == "Right":
                    if id == 8: right_index_finger = (cx, cy)
                elif hand_label == "Left":
                    if id == 4: left_thumb = (cx, cy)
                    if id == 8: left_index = (cx, cy)


    # --- Sol El Ses Kontrolü ---
    if left_thumb and left_index:
        distance = math.hypot(left_index[0] - left_thumb[0], left_index[1] - left_thumb[1])
        volume_level = np.clip((distance - 20) / 130, 0.0, 1.0)
        pygame.mixer.music.set_volume(volume_level)
        cv2.line(img, left_thumb, left_index, (0, 255, 0), 3)

    # --- OpenCV Görüntüsünü Pygame Arka Planı Yapma ---
    # Kameradan gelen görüntüyü döndürüp Pygame'in anlayacağı bir yüzeye (Surface) çeviriyoruz
    img_cam = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_cam = np.rot90(img_cam)
    img_cam = pygame.surfarray.make_surface(img_cam)
    img_cam = pygame.transform.flip(img_cam, True, False)
    
    # Kamerayı tam ekran arka plan olarak basıyoruz
    screen.blit(img_cam, (0, 0))

    # --- Zaman ve Müzik Akış Kontrolü ---
    if music_visualizer_mode and not is_paused:
        now = pygame.time.get_ticks()
        current_pos_seconds += (now - start_ticks) / 1000.0
        start_ticks = now
    else:
        start_ticks = pygame.time.get_ticks()

    if music_visualizer_mode and current_pos_seconds >= song_duration:
        pygame.mixer.music.stop()
        music_visualizer_mode = False
        current_pos_seconds = 0.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Sağ El Buton ve Nokta Dokunma Etkileşimi ---
    if button_pressed_cooldown > 0:
        button_pressed_cooldown -= 1

    if right_index_finger:
        rx, ry = right_index_finger
        if MODE_BUTTON_RECT.collidepoint(rx, ry) and button_pressed_cooldown == 0:
            music_visualizer_mode = not music_visualizer_mode
            button_pressed_cooldown = 15
            if music_visualizer_mode:
                pygame.mixer.music.play(start=current_pos_seconds)
                is_paused = False
            else:
                pygame.mixer.music.stop()
                current_pos_seconds = 0.0

        if not music_visualizer_mode:
            for i, pos in enumerate(duck_positions):
                dist_to_point = math.hypot(rx - pos[0], ry - pos[1])
                if dist_to_point < 25:
                    manual_point_brightness[i] = 255
                else:
                    manual_point_brightness[i] = max(0, manual_point_brightness[i] - 15)

    # --- Hayalet Noktaların Çizilmesi (Yarı Saydam) ---
    current_frame = int(current_pos_seconds * sr / 512)
    vol = normalized_volume[current_frame] if (music_visualizer_mode and current_frame < len(normalized_volume)) else 0

    # Noktalar için şeffaflık destekleyen katman oluşturuyoruz
    points_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    for i, pos in enumerate(duck_positions):
        if music_visualizer_mode:
            r = int(min(20 + vol * (1.0 + (i % 3) * 0.3), 255))
            g = int(min(20 + vol * (0.2 + (i % 4) * 0.4), 255))
            b = int(min(20 + vol * (1.5 - (i % 2) * 0.5), 255))
            radius = int(12 + (vol / 255) * 15)
        else:
            bright = manual_point_brightness[i]
            r = int(bright if i % 3 == 0 else bright * 0.3)
            g = int(bright if i % 3 == 1 else bright * 0.2)
            b = int(bright if i % 3 == 2 else bright * 0.9)
            radius = 15 if bright > 0 else 12

        # Renklerin sonuna ALPHA_VAL ekleyerek "hayalet" (transparan) hale getiriyoruz
        # Dairelerin dışındaki halka parlama efekti
        if r > 20 or g > 20 or b > 20:
            pygame.draw.circle(points_surface, (r // 2, g // 2, b // 2, ALPHA_VAL - 20), pos, radius + 4, width=2)
        # Ana Daire
        pygame.draw.circle(points_surface, (max(20, r), max(20, g), max(20, b), ALPHA_VAL), pos, radius)

    # Şeffaf daire katmanını kameranın üzerine bindiriyoruz
    screen.blit(points_surface, (0, 0))

    # Arayüz Elemanlarını Çiz
    progress = (current_pos_seconds / song_duration) if music_visualizer_mode else 0.0
    draw_player_ui(screen, progress, is_paused, music_visualizer_mode)
    
    pygame.display.flip()
    clock.tick(30)

cap.release()
pygame.quit()
