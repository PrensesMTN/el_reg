import cv2
import HandTrackingModule as htm
import serial
import time

# Arduino seri portu
arduino_port = "/dev/tty.usbmodemXXXX"  # Arduino portunu güncelle
baud_rate = 9600

try:
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Arduino'ya bağlandı: {arduino_port}")
except Exception as e:
    print(f"Seri port hatası: {e}")
    exit()

# Kamera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Kamera açılamadı!")
    exit()

# El detektörü
detector = htm.handDetector(maxHands=1)

# Önceki açı
prev_angle = 90

while True:
    success, img = cap.read()
    if not success:
        break

    img = detector.findHands(img)
    lmList = detector.findPosition(img, z_axis=False)

    if len(lmList) != 0:
        # İşaret parmağı ucu (landmark 8)
        x, y = lmList[8][1], lmList[8][2]

        # Ekran genişliğine göre açı hesapla (0-180)
        angle = int((x / 640) * 180)  # 640 varsayılan genişlik
        angle = max(0, min(180, angle))  # Sınırla

        # Sadece değişiklik varsa gönder
        if abs(angle - prev_angle) > 5:  # 5 derece tolerans
            try:
                ser.write(f"{angle}\n".encode())  # Serial ile gönder
                print(f"Açı gönderildi: {angle}")
                prev_angle = angle
            except Exception as e:
                print(f"Seri port hatası: {e}")

    # Görüntü göster
    cv2.putText(img, f"Aci: {prev_angle}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
    cv2.imshow("El Takibi", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
ser.close()