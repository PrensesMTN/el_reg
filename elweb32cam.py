import cv2
import mediapipe as mp
import requests

# ESP32-CAM IP adresini buraya yaz (Yayın yaptığın stream adresi)
ESP32_URL = "http://http://192.168.1.185/status" 

# MediaPipe El Takibi Kurulumu
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# ESP32-CAM video akışını başlat (Web kamerasından test etmek için 0 yazabilirsin)
cap = cv2.VideoCapture("http://192.168.1.185:81/stream") 
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        continue

    # Görseli RGB'ye çevir (MediaPipe RGB ister)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # El eklemlerini ekrana çiz
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # ÖRNEK MANTIK: İşaret parmağının ucu (Tip) eklemi, alt boğumundan yukarıda mı?
            # Eklemler: 8 = İşaret Parmağı Ucu, 6 = İşaret Parmağı Alt Boğumu
            isaret_ucu = hand_landmarks.landmark[8].y
            isaret_bogum = hand_landmarks.landmark[6].y
            
            if isaret_ucu < isaret_bogum:
                print("Isaret Parmagi ACIK!")
                # requests.get(ESP32_URL + "?servo1=180") -> Robot ele komut gönder
            else:
                print("Isaret Parmagi KAPALI!")
                # requests.get(ESP32_URL + "?servo1=0")

    cv2.imshow("ESP32-CAM El Takibi", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
