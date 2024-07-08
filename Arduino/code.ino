#include <WiFi.h>
#include <WebSocketsServer.h>

const char* ssid = "HA";
const char* password = "12345678";
WebSocketsServer webSocket = WebSocketsServer(81);
float temp;
float humidity;

void webSocketEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  if (type == WStype_TEXT) {
    String receivedMessage = String((char*)payload);
    Serial.println("Received message: " + receivedMessage);
   scanf("%f,%f\r\n",temp,humidity);
  }
}

void setup() {
  Serial.begin(115200);
  delay(10);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println(WiFi.localIP());

  webSocket.begin();
  webSocket.onEvent(webSocketEvent);
}

void loop() {
  webSocket.loop();
}
