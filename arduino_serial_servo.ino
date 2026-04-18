#include <Servo.h>

Servo myServo;
const int servoPin = 9;  // Servo pin (PWM pin)

String inputString = "";  // Gelen veri
bool stringComplete = false;

void setup() {
  Serial.begin(9600);  // Python ile aynı baud rate
  myServo.attach(servoPin);
  myServo.write(90);  // Başlangıç açısı
  Serial.println("Arduino hazır");
}

void loop() {
  // Serial veri oku
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }

  if (stringComplete) {
    Serial.print("Gelen veri: ");
    Serial.println(inputString);  // Gelen veriyi print et

    int angle = inputString.toInt();
    if (angle >= 0 && angle <= 180) {
      myServo.write(angle);
      Serial.print("Servo: ");
      Serial.println(angle);
    } else {
      Serial.println("Hata: Açı 0-180 arası olmalı");
    }
    inputString = "";
    stringComplete = false;
  }
}