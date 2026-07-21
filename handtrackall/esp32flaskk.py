import cv2
import mediapipe as mp
import requests
import time

# ESP32'nin adresleri (Senin çalışan IP'n)
STREAM_URL = "http://192.168.1.126:81/stream"
COMMAND_URL = "http://192.168.1.126/servo" 

# MediaPipe Kurulumu
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.6)

# EKSİK OLAN ÇİZİM ARACI EKLENDİ:
mp_draw = mp.solutions.drawing_utils 

BAS_PARMAK_TIP = 4
son_aci = -1

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

print("Yapay Zeka ve Takip Basladi...")

while True:
    success, frame = cap.read()
    if not success:
        continue

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    bas_parmak_aci = 0 

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            
            # EKSİK OLAN ÇİZİM KOMUTU EKLENDİ (İskeleti ekrana basar):
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Sadece başparmağı kontrol ediyoruz
            if hand_landmarks.landmark[BAS_PARMAK_TIP].x > hand_landmarks.landmark[BAS_PARMAK_TIP - 1].x:
                bas_parmak_aci = 180

    if bas_parmak_aci != son_aci:
        try:
            requests.get(f"{COMMAND_URL}?aci={bas_parmak_aci}", timeout=1)
            print(f"Komut Gonderildi: {bas_parmak_aci} Derece")
            son_aci = bas_parmak_aci
        except requests.exceptions.RequestException as e:
            print("ESP32'ye komut giderken hata olustu!")

    cv2.imshow("Mac Yapay Zeka Merkezi", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()