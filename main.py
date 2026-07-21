import cv2
import numpy as np
import mediapipe as mp
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
app = FastAPI()

# MediaPipe el tespiti modelini başlat
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def calculate_finger_angles(landmarks):
    """
    MediaPipe landmark koordinatlarına göre 5 parmağın açık/kapalı durumunu 
    0 (kapalı) veya 180 (açık) derece olarak hesaplar.
    Parmağın uç noktası (tip) ile eklem noktalarının (pip/mcp) y eksenindeki konumları kıyaslanır.
    """
    # Parmak uçları ve alt eklem indeksleri
    # 4: Başparmak ucu, 8: İşaret ucu, 12: Orta ucu, 16: Yüzük ucu, 20: Serçe ucu
    tips = [4, 8, 12, 16, 20]
    pips = [2, 6, 10, 14, 18] # Karşılaştırma için referans eklemler
    
    angles = {"b": 0, "i": 0, "o": 0, "y": 0, "s": 0}
    keys = ["b", "i", "o", "y", "s"]
    
    for i, (tip, pip) in enumerate(zip(tips, pips)):
        # Resimde y ekseni yukarıdan aşağıya artar. 
        # Uç nokta eklemden yukarıdaysa (y koordineti daha küçükse) parmak açıktır.
        if i == 0:
            # Başparmak yatay eksende hareket ettiği için x koordinatına bakılır
            if landmarks[tip].x > landmarks[pip].x:
                angles[keys[i]] = 180
            else:
                angles[keys[i]] = 0
        else:
            # Diğer 4 parmak dikey eksende kontrol edilir
            if landmarks[tip].y < landmarks[pip].y:
                angles[keys[i]] = 180
            else:
                angles[keys[i]] = 0
                
    return angles

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-CAM başarıyla bağlandı!")
    try:
        while True:
            # ESP32-CAM'den gelen JPEG bayt verisini al
            bytes_data = await websocket.receive_bytes()
            
            # OpenCV formatına dönüştür
            np_arr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # RGB formatına çevir
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                
                # Varsayılan motor açıları (Tüm parmaklar kapalı)
                motor_angles = {"b": 0, "i": 0, "o": 0, "y": 0, "s": 0}
                
                # El algılandıysa parmak açılarını hesapla
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        motor_angles = calculate_finger_angles(hand_landmarks.landmark)
                
                # Hesaplanan açıları JSON olarak ESP32-CAM'e gönder
                await websocket.send_json(motor_angles)
                
    except WebSocketDisconnect:
        print("ESP32-CAM bağlantısı koptu.")
    except Exception as e:
        print(f"Hata oluştu: {e}")