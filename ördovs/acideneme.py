import requests
import time

# ESP32 seri ekranında yazan IP adresini buraya gir
esp32_ip = "192.168.1.212"  # Örnektir, sendekini yaz!
url = f"http://{esp32_ip}/servo"

def servo_gonder(aci):
    try:
        payload = {'angle': aci}
        response = requests.get(url, params=payload, timeout=2)
        print(f"Yanıt: {response.text}")
    except Exception as e:
        print(f"Bağlantı hatası: {e}")

while True:
    aci_girisi = input("Açı girin (0-180) veya 'q' ile çıkın: ")
    if aci_girisi.lower() == 'q':
        break
    
    if aci_girisi.isdigit():
        servo_gonder(aci_girisi)
    else:
        print("Lütfen geçerli bir sayı girin.")