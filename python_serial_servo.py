import serial
import time

# Arduino seri portu (macOS'ta /dev/tty.usbmodemXXXX gibi)
arduino_port = "/dev/tty.usbmodemXXXX"  # Arduino'nun portunu bul (Arduino IDE'de Tools > Port)
baud_rate = 9600

try:
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    print(f"Arduino'ya bağlandı: {arduino_port}")
except Exception as e:
    print(f"Seri port hatası: {e}")
    exit()

def servo_gonder(angle):
    if 0 <= angle <= 180:
        ser.write(f"{angle}\n".encode())  # Açıyı gönder
        print(f"Açı gönderildi: {angle}")
        time.sleep(0.1)  # Kısa bekle
    else:
        print("Açı 0-180 arası olmalı")

while True:
    try:
        angle = int(input("Servo açısı (0-180) veya 'q' çık: "))
        if angle == 'q':
            break
        servo_gonder(angle)
    except ValueError:
        print("Geçerli sayı girin")

ser.close()
print("Çıkış")