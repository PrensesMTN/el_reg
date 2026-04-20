from http.server import BaseHTTPRequestHandler, HTTPServer
import cv2
import HandTrackingModule as htm
import time
import threading



"""
class ServoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/angle':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(current_angle).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', 8080)  # Tüm IP'lerde 8080 port
    httpd = HTTPServer(server_address, ServoHandler)
    print("Server başladı: http://localhost:8080/angle")
    httpd.serve_forever()

# Kamera ve el takibi
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı!")
    exit()

detector = htm.handDetector(maxHands=1)
prev_angle = 90

# Server'i ayrı thread'de çalıştır
import threading
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)  # Ayna görüntüsü için yatay çevir

    img = detector.findHands(img)
    lmList = detector.findPosition(img, z_axis=False)

    if len(lmList) >= 9:  # Landmark 8 ve 5 var mı kontrol
        # İşaret parmağı ucu (8) ve taban (5)
        x8, y8 = lmList[8][1], lmList[8][2]
        x5, y5 = lmList[5][1], lmList[5][2]

        # Mesafe hesapla
        distance = ((x8 - x5)**2 + (y8 - y5)**2)**0.5

        # Mesafeye göre açı (örnek: mesafe > 100 ise açık = 180, değilse kapalı = 0)
        if distance > 100:
            angle = 0  # Parmak açık
        else:
            angle = 120    # Parmak kapalı

        if angle != prev_angle:
            current_angle = angle  # Global değişkeni güncelle
            print(f"Parmak durumu: {'Açık' if angle == 180 else 'Kapalı'} - Açı: {angle}")
            prev_angle = angle

    cv2.putText(img, f"Aci: {current_angle}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    cv2.imshow("El Takibi", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()"""


# Global açı değişkenleri
current_angle_isaret = 90
current_angle_bas = 90

class ServoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/angle':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # İki açıyı yan yana gönderiyoruz: "isaret,basparmak"
            output = f"{current_angle_isaret},{current_angle_bas}"
            self.wfile.write(output.encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, ServoHandler)
    print("Server başladı: http://localhost:8080/angle")
    httpd.serve_forever()

# Server'ı başlat
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

cap = cv2.VideoCapture(0)
detector = htm.handDetector(maxHands=1)

while True:
    success, img = cap.read()
    if not success: break

    img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList = detector.findPosition(img, z_axis=False)

    if len(lmList) >= 21:  # Tüm el noktaları varsa
        # --- İŞARET PARMAĞI ---
        dist_isaret = ((lmList[8][1]-lmList[5][1])**2 + (lmList[8][2]-lmList[5][2])**2)**0.5
        current_angle_isaret = 0 if dist_isaret > 100 else 120

        # --- BAŞPARMAK ---
        # 4: Başparmak ucu, 2: Başparmak boğumu
        dist_bas = ((lmList[4][1]-lmList[2][1])**2 + (lmList[4][2]-lmList[2][2])**2)**0.5
        current_angle_bas = 0 if dist_bas > 70 else 120 

     

    cv2.putText(img, f"Isaret: {current_angle_isaret} Bas: {current_angle_bas}", 
                (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 3)
    cv2.imshow("El Takibi", img)

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()