import cv2
import mediapipe as mp

# MediaPipe ayarları
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, image = cap.read()
    if not success:
        break

    # Görüntüyü yansıt (ayna etkisi) ve RGB'ye çevir
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
    
    # El tespiti yap
    results = hands.process(image)

    # Görüntüyü tekrar BGR'ye çevir (OpenCV için)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Eklemleri ekrana çiz
            mp_drawing.draw_landmarks(
                image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Örnek: İşaret parmağının ucunun koordinatlarını al (8. nokta)
            # x = hand_landmarks.landmark[8].x
            # y = hand_landmarks.landmark[8].y
            # print(f"İşaret Parmağı: {x}, {y}")

    cv2.imshow('MediaPipe Hand Tracking', image)

    if cv2.waitKey(5) & 0xFF == 27: # ESC ile çıkış
        break

cap.release()
cv2.destroyAllWindows()