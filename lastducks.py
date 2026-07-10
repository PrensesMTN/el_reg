"""import pygame
import numpy as np
import librosa
import cv2
import mediapipe as mp
import math
import sys
import random

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

if sys.platform.startswith('win'):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(0)

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

duck_positions = [
    (320, 50), (400, 150), (240, 150), (480, 250), (320, 250), 
    (160, 250), (560, 350), (400, 350), (240, 350), (80, 350)
]

manual_point_brightness = [0] * 10

BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 430, 50, 35)
BAR_RECT = pygame.Rect(50, 405, SCREEN_WIDTH - 100, 10)
MODE_BUTTON_RECT = pygame.Rect(480, 15, 140, 40)

# Arayüz şeffaflığı artık sağ ele bağlı değil, sabit bir görünürlükte tutuluyor
UI_ALPHA = 180  

def draw_player_ui(screen, progress, is_paused, mode_active, current_alpha):
    ui_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(ui_surface, (60, 60, 65, current_alpha), BAR_RECT, border_radius=5)
    
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 40)), filled_bar, border_radius=5)
        pygame.draw.circle(ui_surface, (220, 220, 220, min(255, current_alpha + 40)), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 6)

    pygame.draw.rect(ui_surface, (40, 40, 45, current_alpha), BUTTON_RECT, border_radius=5)
    if is_paused:
        pygame.draw.polygon(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), [(BUTTON_RECT.x + 18, BUTTON_RECT.y + 8), (BUTTON_RECT.x + 18, BUTTON_RECT.y + 27), (BUTTON_RECT.x + 35, BUTTON_RECT.y + 17)])
    else:
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), (BUTTON_RECT.x + 16, BUTTON_RECT.y + 9, 5, 18))
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 9, 5, 18))

    btn_color = (0, 180, 100, min(255, current_alpha + 20)) if mode_active else (180, 50, 50, min(255, current_alpha + 20))
    pygame.draw.rect(ui_surface, btn_color, MODE_BUTTON_RECT, border_radius=8)
    
    font = pygame.font.SysFont("Arial", 14, bold=True)
    text_str = "RITIM MODU" if mode_active else "DOKUNMA MODU"
    text_surface = font.render(text_str, True, (255, 255, 255))
    
    screen.blit(ui_surface, (0, 0))
    screen.blit(text_surface, (MODE_BUTTON_RECT.x + 15, MODE_BUTTON_RECT.y + 12))

while running:
    if not pygame.display.get_init():
        break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
            
    if not running:
        break

    success, img = cap.read()
    if not success:
        img = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
        
    img = cv2.flip(img, 1) 
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    right_index_finger = None
    right_thumb = None
    left_thumb = None
    left_index = None

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_lms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            hand_label = handedness.classification[0].label
            
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * SCREEN_WIDTH), int(lm.y * SCREEN_HEIGHT)
                if hand_label == "Right":
                    if id == 4: right_thumb = (cx, cy)
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

    # --- Sağ El Sadece Tıklama (Çizgi ve Alpha müdahalesi kaldırıldı) ---
    is_right_clicking = False
    if right_thumb and right_index_finger:
        right_dist = math.hypot(right_index_finger[0] - right_thumb[0], right_index_finger[1] - right_thumb[1])
        if right_dist < 25:
            is_right_clicking = True

    # --- OpenCV Görüntüsünü Pygame Arka Planı Yapma ---
    img_cam = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_cam = np.rot90(img_cam)
    img_cam = pygame.surfarray.make_surface(img_cam)
    img_cam = pygame.transform.flip(img_cam, True, False)
    
    if not pygame.display.get_init():
        break
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

    # --- Sağ El Buton ve Nokta Dokunma Etkileşimi ---
    if button_pressed_cooldown > 0:
        button_pressed_cooldown -= 1

    if right_index_finger:
        rx, ry = right_index_finger
        
        if MODE_BUTTON_RECT.collidepoint(rx, ry) and is_right_clicking and button_pressed_cooldown == 0:
            music_visualizer_mode = not music_visualizer_mode
            button_pressed_cooldown = 20
            if music_visualizer_mode:
                pygame.mixer.music.play(start=current_pos_seconds)
                is_paused = False
            else:
                pygame.mixer.music.stop()
                current_pos_seconds = 0.0

        elif BUTTON_RECT.collidepoint(rx, ry) and is_right_clicking and button_pressed_cooldown == 0:
            button_pressed_cooldown = 20
            if is_paused:
                pygame.mixer.music.unpause()
                is_paused = False
            else:
                pygame.mixer.music.pause()
                is_paused = True

        elif BAR_RECT.collidepoint(rx, ry) and is_right_clicking:
            clicked_ratio = (rx - BAR_RECT.x) / BAR_RECT.width
            current_pos_seconds = clicked_ratio * song_duration
            pygame.mixer.music.play(start=current_pos_seconds)
            if is_paused:
                pygame.mixer.music.pause()

        if not music_visualizer_mode:
            for i, pos in enumerate(duck_positions):
                dist_to_point = math.hypot(rx - pos[0], ry - pos[1])
                if dist_to_point < 25:
                    manual_point_brightness[i] = 255
                else:
                    manual_point_brightness[i] = max(0, manual_point_brightness[i] - 15)

    # --- Hayalet Noktaların Çizilmesi ---
    current_frame = int(current_pos_seconds * sr / 512)
    vol = normalized_volume[current_frame] if (music_visualizer_mode and current_frame < len(normalized_volume)) else 0

    points_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    for i, pos in enumerate(duck_positions):
        final_x, final_y = pos[0], pos[1]

        if music_visualizer_mode:
            # Müziğin şiddetine (vol) göre dinamik renk ve parlaklık
            base_val = int((vol / 255) * 200) + 55  
            
            r = min(255, base_val if i % 3 == 0 else int(base_val * 0.3))
            g = min(255, base_val if i % 3 == 1 else int(base_val * 0.3))
            b = min(255, base_val if i % 3 == 2 else int(base_val * 0.3))

            # Bas vuruşlarında anlık tam beyaz parlama (Strobe/Flaş efekti)
            if vol > 200:
                r, g, b = 255, 255, 255

            radius = int(12 + (vol / 255) * 20)
            
            # Ritime göre titreme
            shake_intensity = int((vol / 255) * 6)
            if shake_intensity > 0:
                final_x += random.randint(-shake_intensity, shake_intensity)
                final_y += random.randint(-shake_intensity, shake_intensity)

            # Ördeklerin doğrudan ritimle çizimi
            pygame.draw.circle(points_surface, (r, g, b, 255), (final_x, final_y), radius)
            # Dış hale efekti (Ritim arttıkça büyür ve belirginleşir)
            pygame.draw.circle(points_surface, (r, g, b, 120), (final_x, final_y), radius + 6, width=2)

        else:
            bright = manual_point_brightness[i]
            r = int(bright if i % 3 == 0 else bright * 0.3)
            g = int(bright if i % 3 == 1 else bright * 0.2)
            b = int(bright if i % 3 == 2 else bright * 0.9)
            radius = 15 if bright > 0 else 12
            use_alpha = 150

            if r > 20 or g > 20 or b > 20:
                pygame.draw.circle(points_surface, (r // 2, g // 2, b // 2, max(0, 50)), (final_x, final_y), radius + 4, width=2)
            pygame.draw.circle(points_surface, (max(20, r), max(20, g), max(20, b), use_alpha), (final_x, final_y), radius)

    if pygame.display.get_init():
        screen.blit(points_surface, (0, 0))

    # Arayüz Elemanlarını Çiz
    progress = (current_pos_seconds / song_duration) if music_visualizer_mode else 0.0
    draw_player_ui(screen, progress, is_paused, music_visualizer_mode, UI_ALPHA)

    if pygame.display.get_init():
        pygame.display.flip()

    clock.tick(30)

cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()"""
import pygame
import numpy as np
import librosa
import cv2
import mediapipe as mp
import math
import sys
import random
import colorsys # Renk kaydırma (Hue shift) işlemi için eklendi

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

if sys.platform.startswith('win'):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(0)

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

duck_positions = [
    (320, 50), (400, 150), (240, 150), (480, 250), (320, 250), 
    (160, 250), (560, 350), (400, 350), (240, 350), (80, 350)
]

manual_point_brightness = [0] * 10

BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 25, 430, 50, 35)
BAR_RECT = pygame.Rect(50, 405, SCREEN_WIDTH - 100, 10)
MODE_BUTTON_RECT = pygame.Rect(480, 15, 140, 40)

UI_ALPHA = 180  

def draw_player_ui(screen, progress, is_paused, mode_active, current_alpha):
    ui_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(ui_surface, (60, 60, 65, current_alpha), BAR_RECT, border_radius=5)
    
    progress_width = int(BAR_RECT.width * progress)
    if progress_width > 0:
        filled_bar = pygame.Rect(BAR_RECT.x, BAR_RECT.y, progress_width, BAR_RECT.height)
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 40)), filled_bar, border_radius=5)
        pygame.draw.circle(ui_surface, (220, 220, 220, min(255, current_alpha + 40)), (BAR_RECT.x + progress_width, BAR_RECT.y + BAR_RECT.height // 2), 6)

    pygame.draw.rect(ui_surface, (40, 40, 45, current_alpha), BUTTON_RECT, border_radius=5)
    if is_paused:
        pygame.draw.polygon(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), [(BUTTON_RECT.x + 18, BUTTON_RECT.y + 8), (BUTTON_RECT.x + 18, BUTTON_RECT.y + 27), (BUTTON_RECT.x + 35, BUTTON_RECT.y + 17)])
    else:
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), (BUTTON_RECT.x + 16, BUTTON_RECT.y + 9, 5, 18))
        pygame.draw.rect(ui_surface, (200, 200, 200, min(255, current_alpha + 50)), (BUTTON_RECT.x + 29, BUTTON_RECT.y + 9, 5, 18))

    btn_color = (0, 180, 100, min(255, current_alpha + 20)) if mode_active else (180, 50, 50, min(255, current_alpha + 20))
    pygame.draw.rect(ui_surface, btn_color, MODE_BUTTON_RECT, border_radius=8)
    
    font = pygame.font.SysFont("Arial", 14, bold=True)
    text_str = "RITIM MODU" if mode_active else "DOKUNMA MODU"
    text_surface = font.render(text_str, True, (255, 255, 255))
    
    screen.blit(ui_surface, (0, 0))
    screen.blit(text_surface, (MODE_BUTTON_RECT.x + 15, MODE_BUTTON_RECT.y + 12))

while running:
    if not pygame.display.get_init():
        break

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
            
    if not running:
        break

    success, img = cap.read()
    if not success:
        img = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
        
    img = cv2.flip(img, 1) 
    h, w, c = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    
    right_index_finger = None
    right_thumb = None
    left_thumb = None
    left_index = None

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_lms, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            mp_draw.draw_landmarks(img, hand_lms, mp_hands.HAND_CONNECTIONS)
            hand_label = handedness.classification[0].label
            
            for id, lm in enumerate(hand_lms.landmark):
                cx, cy = int(lm.x * SCREEN_WIDTH), int(lm.y * SCREEN_HEIGHT)
                if hand_label == "Right":
                    if id == 4: right_thumb = (cx, cy)
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

    # --- Sağ El Tıklama ve Mor Çizgi Mantığı ---
    is_right_clicking = False
    current_right_dist = 0  # Renk kaydırması için mesafeyi saklayacağız
    
    if right_thumb and right_index_finger:
        right_dist = math.hypot(right_index_finger[0] - right_thumb[0], right_index_finger[1] - right_thumb[1])
        current_right_dist = right_dist
        
        if right_dist < 25:
            is_right_clicking = True
            
        # Ritim modundaysa işaret ve baş parmak arasına MOR çizgi çek
        if music_visualizer_mode:
            # OpenCV BGR formatında çalıştığı için (255, 0, 255) Magenta/Mor rengini verir
            cv2.line(img, right_thumb, right_index_finger, (255, 0, 255), 3)

    # --- OpenCV Görüntüsünü Pygame Arka Planı Yapma ---
    img_cam = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_cam = np.rot90(img_cam)
    img_cam = pygame.surfarray.make_surface(img_cam)
    img_cam = pygame.transform.flip(img_cam, True, False)
    
    if not pygame.display.get_init():
        break
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

    # --- Sağ El Buton ve Nokta Dokunma Etkileşimi ---
    if button_pressed_cooldown > 0:
        button_pressed_cooldown -= 1

    if right_index_finger:
        rx, ry = right_index_finger
        
        if MODE_BUTTON_RECT.collidepoint(rx, ry) and is_right_clicking and button_pressed_cooldown == 0:
            music_visualizer_mode = not music_visualizer_mode
            button_pressed_cooldown = 20
            if music_visualizer_mode:
                pygame.mixer.music.play(start=current_pos_seconds)
                is_paused = False
            else:
                pygame.mixer.music.stop()
                current_pos_seconds = 0.0

        elif BUTTON_RECT.collidepoint(rx, ry) and is_right_clicking and button_pressed_cooldown == 0:
            button_pressed_cooldown = 20
            if is_paused:
                pygame.mixer.music.unpause()
                is_paused = False
            else:
                pygame.mixer.music.pause()
                is_paused = True

        elif BAR_RECT.collidepoint(rx, ry) and is_right_clicking:
            clicked_ratio = (rx - BAR_RECT.x) / BAR_RECT.width
            current_pos_seconds = clicked_ratio * song_duration
            pygame.mixer.music.play(start=current_pos_seconds)
            if is_paused:
                pygame.mixer.music.pause()

        if not music_visualizer_mode:
            for i, pos in enumerate(duck_positions):
                dist_to_point = math.hypot(rx - pos[0], ry - pos[1])
                if dist_to_point < 25:
                    manual_point_brightness[i] = 255
                else:
                    manual_point_brightness[i] = max(0, manual_point_brightness[i] - 15)

    # --- Hayalet Noktaların Çizilmesi ---
    current_frame = int(current_pos_seconds * sr / 512)
    vol = normalized_volume[current_frame] if (music_visualizer_mode and current_frame < len(normalized_volume)) else 0

    points_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    for i, pos in enumerate(duck_positions):
        final_x, final_y = pos[0], pos[1]

        if music_visualizer_mode:
            # 1. Ritime bağlı PARLAKLIK (Value) (0.3 ile 1.0 arası)
            brightness = min(1.0, (vol / 255.0) * 0.7 + 0.3)
            
            # 2. Temel Renk Tonu (Hue): Ördeklerin indeksine göre (Kırmızı, Yeşil, Mavi)
            base_hue = (i % 3) * 0.333
            
            # 3. Sağ el mor çizgisinin uzunluğuna göre RENK KAYDIRMA (Hue Shift)
            # Parmaklar 25px kapalıyken renk kayması 0'dır, 200px açıkken renkler tam tur atar.
            color_shift = np.clip((current_right_dist - 25) / 175.0, 0.0, 1.0)
            
            # Yeni rengi hesapla
            final_hue = (base_hue + color_shift) % 1.0
            
            # HSV'yi RGB'ye çevirerek renkleri elde et
            r_f, g_f, b_f = colorsys.hsv_to_rgb(final_hue, 0.85, brightness)
            r, g, b = int(r_f * 255), int(g_f * 255), int(b_f * 255)

            # Bas vuruşlarında anlık tam beyaz parlama (Strobe/Flaş efekti) hala ritme bağlı çalışır
            if vol > 200:
                r, g, b = 255, 255, 255

            radius = int(12 + (vol / 255) * 20)
            
            # Ritime göre titreme
            shake_intensity = int((vol / 255) * 6)
            if shake_intensity > 0:
                final_x += random.randint(-shake_intensity, shake_intensity)
                final_y += random.randint(-shake_intensity, shake_intensity)

            # Çizim
            pygame.draw.circle(points_surface, (r, g, b, 255), (final_x, final_y), radius)
            pygame.draw.circle(points_surface, (r, g, b, 120), (final_x, final_y), radius + 6, width=2)

        else:
            bright = manual_point_brightness[i]
            r = int(bright if i % 3 == 0 else bright * 0.3)
            g = int(bright if i % 3 == 1 else bright * 0.2)
            b = int(bright if i % 3 == 2 else bright * 0.9)
            radius = 15 if bright > 0 else 12
            use_alpha = 150

            if r > 20 or g > 20 or b > 20:
                pygame.draw.circle(points_surface, (r // 2, g // 2, b // 2, max(0, 50)), (final_x, final_y), radius + 4, width=2)
            pygame.draw.circle(points_surface, (max(20, r), max(20, g), max(20, b), use_alpha), (final_x, final_y), radius)

    if pygame.display.get_init():
        screen.blit(points_surface, (0, 0))

    # Arayüz Elemanlarını Çiz
    progress = (current_pos_seconds / song_duration) if music_visualizer_mode else 0.0
    draw_player_ui(screen, progress, is_paused, music_visualizer_mode, UI_ALPHA)

    if pygame.display.get_init():
        pygame.display.flip()

    clock.tick(30)

cap.release()
cv2.destroyAllWindows()
pygame.quit()
sys.exit()