"""import cv2
import os

# 1. Adım: Kamerayı başlat
vid = cv2.VideoCapture(0)

# 2. Adım: Cascade dosyasının yolunu buraya yapıştır
# Kopyaladığın yolu tırnak içine koy. Örnek: "/Users/prenses/Documents/hand/cascade.xml"()### CASCADE DOSYASININ YOLU)

cascade_path = "C:\\Users\\prenses\\Documents\\hand \\catcascade\\classifier\\cascade.xml" 

if not os.path.exists(cascade_path):
    print(f"HATA: {cascade_path} dosyası bulunamadı! Lütfen yolu kontrol et.")
else:
    face_cascade = cv2.CascadeClassifier(cascade_path)

font1 = cv2.FONT_HERSHEY_SIMPLEX 

while True:
    ret, frame = vid.read()
    
    # Görüntü boşsa (kamera henüz açılmadıysa) hata vermemesi için başa dön
    if not ret:
        print("Kameradan görüntü bekleniyor...")
        continue

    frame = cv2.flip(frame, 1)
    
    # Gri tonlamaya çevir
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Nesne tespiti
    kedi = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in kedi:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        cv2.putText(frame, "kedi", (x, y), font1, 1, (255, 0, 255), cv2.LINE_4)

    cv2.imshow('Kedi Takip Sistemi', frame)
    
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

vid.release()
cv2.destroyAllWindows()"""
import cv2

# Kamerayı başlat
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# Kamera gerçekten açıldı mı kontrol et
if not cap.isOpened():
    print("HATA: Kamera yolu açık ama görüntü alınamıyor.")
else:
    print("Kamera başarıyla bağlandı! Kapatmak için 'q' tuşuna bas.")

while True:
    ret, frame = cap.read()

    # Eğer bir anlık görüntü gelmezse hata vermemesi için:
    if not ret or frame is None:
        continue

    # Görüntüyü aynala (Daha doğal bir kullanım için)
    frame = cv2.flip(frame, 1)

    # Ekranda göster
    cv2.imshow('Anam Babam Usulu Kamera', frame)

    # 'q' tuşuna basınca her şeyi kapat
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizlik vakti
cap.release()
cv2.destroyAllWindows()
