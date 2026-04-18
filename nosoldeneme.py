import cv2
vid=cv2.VideoCapture(0)
face_cascade=cv2.CascadeClassifier(r"C:\Users\prems\Desktop\opencv_blog_content-master\classifier\cascade.xml")### CASCADE DOSYASININ YOLU)
font1 = cv2.FONT_HERSHEY_SIMPLEX # YAKALANAN GÖRSELİN ADININ FONTU
while True:
   ret,frame = vid.read()
   frame=cv2.flip(frame,1)
   gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

   kedi=face_cascade.detectMultiScale(gray,1.3,5)# daha iyi sonuç almak için parametrelerle oyna
   ##if not getting good result try to train new cascade.xml file again deleting other file expect p and n in temp folder

   for(x,y,w,h) in kedi:
      cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
      cv2.putText(frame,"kedi",(x,y),font1,1,(255,0,255),cv2.LINE_4)

   
   cv2.imshow('kedi',frame)
   
   if cv2.waitKey(1)  & 0xFF==ord("q"):
       break
vid.release()
cv2.destroyAllWindows()
