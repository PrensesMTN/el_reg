import cv2
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Küçük yardımcı endpoint: sunucunun çalışıp çalışmadığını hızlıca kontrol etmek için
@app.get("/")
async def root():
    return {"status": "ok"}

# MediaPipe el tespiti modelini başlat
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False, 
    max_num_hands=1, 
    min_detection_confidence=0.5
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ESP32-CAM bağlandı!")
    try:
        while True:
            bytes_data = await websocket.receive_bytes()
            np_arr = np.frombuffer(bytes_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb_frame)
                
                motor_angles = {"b": 0, "i": 0, "o": 0, "y": 0, "s": 0}
                
                if results.multi_hand_landmarks:
                    motor_angles = {"b": 180, "i": 180, "o": 180, "y": 180, "s": 180} 
                
                await websocket.send_json(motor_angles)
                
    except WebSocketDisconnect:
        print("ESP32-CAM bağlantısı koptu.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")


if __name__ == "__main__":
    import uvicorn

    # Bu dosyayı doğrudan `python main.py` ile çalıştırmak isterseniz
    # aşağıdaki satır sunucuyu başlatır. Uvicorn ile çalıştırırken
    # `uvicorn main:app --reload` komutunu kullanabilirsiniz.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)