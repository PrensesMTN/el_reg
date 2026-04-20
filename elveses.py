import cv2
import mediapipe as mp
import math
import numpy as np
import pygame
import os

# macOS Çakışma Önleyici
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# --- 1. Ses Ayarları ve Liste Oluşturma ---
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

# Ses dosyalarını bir liste olarak tanımla
# NOT: Bu dosyaların klasöründe olduğundan emin ol!
ses_listesi = ["ses.mp3", "Interstellar_Theme.mp3"]
su_anki_ses_id = 0

def ses_yukle(index):
    try:
        return pygame.mixer.Sound(ses_listesi[index])
    except:
        print(f"Hata: {ses_listesi[index]} bulunamadı!")
        return None

current_sound = ses_yukle(su_anki_ses_id)
channel = pygame.mixer.Channel(0)

# --- 2. MediaPipe ve Değişkenler ---
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

cap = cv2.VideoCapture(0)

# Parmak ID'leri
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12

# Değişim kilidi (Sesin sürekli takılmaması için)
degisim_kilidi = False

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    right_hand_dist_index = 100 
    right_hand_dist_middle = 100
    left_hand_dist = 100 

    if results.multi_hand_landmarks:
        for idx, hand_lms in enumerate(results.multi_hand_landmarks):
            # El Çizgilerini Çiz
            mp_drawing.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS,
                                    mp_drawing_styles.get_default_hand_landmarks_style(),
                                    mp_drawing_styles.get_default_hand_connections_style())

            label = results.multi_handedness[idx].classification[0].label
            
            # Parmak uçlarını al
            t = hand_lms.landmark[THUMB_TIP]
            i = hand_lms.landmark[INDEX_TIP]
            m = hand_lms.landmark[MIDDLE_TIP]
            
            # Koordinatlar
            t_px = (int(t.x * w), int(t.y * h))
            i_px = (int(i.x * w), int(i.y * h))
            m_px = (int(m.x * w), int(m.y * h))

            if label == "Right":
                # Sağ El Mesafeleri
                right_hand_dist_index = math.hypot(t.x - i.x, t.y - i.y) * 100
                right_hand_dist_middle = math.hypot(t.x - m.x, t.y - m.y) * 100
                
                # İşaret parmağı bağlantısı (Mavi)
                cv2.line(frame, t_px, i_px, (255, 0, 0), 3)
                # Orta parmak bağlantısı (Sarı)
                cv2.line(frame, t_px, m_px, (0, 255, 255), 3)
            else:
                # Sol El Mesafesi (Ses Seviyesi)
                left_hand_dist = math.hypot(t.x - i.x, t.y - i.y) * 100
                cv2.line(frame, t_px, i_px, (0, 255, 0), 3)

        # --- SES KONTROLÜ ---
        
        # 1. Ses Değiştirme (Sağ El: Başparmak + Orta Parmak)
        if right_hand_dist_middle < 5:
            if not degisim_kilidi:
                su_anki_ses_id = (su_anki_ses_id + 1) % len(ses_listesi)
                current_sound = ses_yukle(su_anki_ses_id)
                if channel.get_busy(): # Eğer ses çalıyorsa yenisiyle devam et
                    channel.play(current_sound, loops=-1)
                print(f"Ses Değişti: {ses_listesi[su_anki_ses_id]}")
                degisim_kilidi = True # Parmak ayrılana kadar bir daha değiştirme
        else:
            degisim_kilidi = False

        # 2. Oynat/Durdur (Sağ El: Başparmak + İşaret Parmağı)
        if right_hand_dist_index < 5:
            if not channel.get_busy() and current_sound:
                channel.play(current_sound, loops=-1)
        elif right_hand_dist_index > 10:
            channel.stop()

        # 3. Ses Seviyesi (Sol El)
        if channel.get_busy():
            vol = np.interp(left_hand_dist, [5, 40], [0.0, 1.0])
            channel.set_volume(vol)

    # Bilgileri Yaz
    cv2.putText(frame, f"Aktif Ses: {ses_listesi[su_anki_ses_id]}", (10, 30), 1, 1.5, (0,255,255), 2)
    
    cv2.imshow("Multi-Sound Theremin", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()