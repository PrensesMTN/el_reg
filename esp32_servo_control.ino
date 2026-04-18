
#include <ESP8266WiFi.h>
#include <Servo.h>

const char* ssid = "TeknoSanat_Kopru";
const char* password = "teknosanat.26";
const char* serverIP = "192.168.1.240";  // Python server IP'si
const int serverPort = 8080;

WiFiClient client;
Servo myservo;

void setup() {
  Serial.begin(115200);
  myservo.attach(D2);
  myservo.write(90);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi bağlandı!");
  Serial.print("ESP IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (client.connect(serverIP, serverPort)) {
    client.println("GET /angle HTTP/1.0");
    client.println("Host: " + String(serverIP));
    client.println("Connection: close");
    client.println();

    String response = "";
    while (client.connected() || client.available()) {
      if (client.available()) {
        char c = client.read();
        response += c;
      }
    }
    client.stop();

    // Response'dan açı çıkar
    int bodyIndex = response.indexOf("\r\n\r\n");
    if (bodyIndex > 0) {
      String body = response.substring(bodyIndex + 4);
      int angle = body.toInt();
      if (angle >= 0 && angle <= 180) {
        myservo.write(angle);
        Serial.print("Açı set edildi: ");
        Serial.println(angle);
      }
    }
  } else {
    Serial.println("Bağlantı başarısız");
  }

  delay(1000);  // 1 saniye bekle
}
