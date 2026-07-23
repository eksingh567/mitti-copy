/*
 * MITTI — Soil Intelligence System
 * ESP32 Version — 3 Separate MAX485 Modules
 * Samsung Solve for Tomorrow 2025
 *
 * MAX485 #1 (NPK):      RX=16, TX=17, DE/RE=4
 * MAX485 #2 (Moisture): RX=18, TX=19, DE/RE=5
 * MAX485 #3 (EC):       RX=13, TX=15, DE/RE=23
 * pH Probe:             GPIO34
 * DHT11:                GPIO27
 * MQ-135 AO:            GPIO33
 * MQ-135 DO:            GPIO14
 * Rain AO:              GPIO35
 * Rain DO:              GPIO26
 * Water Level:          GPIO32
 * Relay (Pump):         GPIO25
 * LCD I2C:              SDA=21, SCL=22
 */

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <WiFi.h>
#include <HTTPClient.h>

// ─── WiFi ────────────────────────────────────────────
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL    = "http://YOUR_SERVER_IP:5000/data";

// ─── Pins ─────────────────────────────────────────────
// MAX485 #1 — NPK
#define NPK_RX        16
#define NPK_TX        17
#define NPK_DE_RE     4

// MAX485 #2 — Moisture
#define MOIST_RX      18
#define MOIST_TX      19
#define MOIST_DE_RE   5

// MAX485 #3 — EC
#define EC_RX         13
#define EC_TX         15
#define EC_DE_RE      23

// Analog / Digital
#define PH_PIN        34
#define DHT_PIN       27
#define MQ135_AO      33
#define MQ135_DO      14
#define RAIN_AO       35
#define RAIN_DO       26
#define WATER_LVL     32
#define RELAY_PIN     25

// ─── Thresholds ───────────────────────────────────────
#define MOISTURE_LOW  30
#define MOISTURE_HIGH 70
#define TANK_EMPTY    500
#define NH3_ALARM     600

// ─── Objects ──────────────────────────────────────────
HardwareSerial NPK_Serial(1);    // UART1
HardwareSerial MOIST_Serial(2);  // UART2
// For EC we use a Software approach via UART1 reassigned
// Actually ESP32 has UART0,1,2 — we'll use all 3

// Wait — ESP32 only has 3 UARTs (0,1,2)
// UART0 = USB (Serial) - don't reassign
// UART1 = reassignable → NPK
// UART2 = reassignable → Moisture
// For EC: use SoftwareSerial emulation via bit-bang OR share UART2 with address

// SOLUTION: Use UART1 for NPK, UART2 for Moisture, SoftwareSerial for EC
#include <SoftwareSerial.h>
SoftwareSerial EC_Serial(EC_RX, EC_TX);

LiquidCrystal_I2C lcd(0x27, 20, 4);
DHT dht(DHT_PIN, DHT11);

// ─── Sensor Data ──────────────────────────────────────
float nitrogen    = 0;
float phosphorus  = 0;
float potassium   = 0;
float moisture    = 0;
float ec          = 0;
float ph          = 0;
float temperature = 0;
float humidity    = 0;
int   mq135_val   = 0;
int   rain_val    = 0;
int   water_val   = 0;
bool  raining     = false;
bool  pump_on     = false;

int  lcdPage      = 0;
unsigned long lastRead = 0;
unsigned long lastLCD  = 0;
unsigned long lastSend = 0;

// ─── CRC16 Modbus ─────────────────────────────────────
uint16_t calcCRC(uint8_t* buf, int len) {
  uint16_t crc = 0xFFFF;
  for (int i = 0; i < len; i++) {
    crc ^= buf[i];
    for (int j = 0; j < 8; j++)
      crc = (crc & 1) ? (crc >> 1) ^ 0xA001 : crc >> 1;
  }
  return crc;
}

// ─── Generic RS485 Read ───────────────────────────────
template <typename T>
bool rs485Read(T &serial, int dePin, uint8_t addr,
               uint16_t reg, uint8_t count, uint16_t* out) {
  while (serial.available()) serial.read(); // flush

  uint8_t cmd[8];
  cmd[0] = addr; cmd[1] = 0x03;
  cmd[2] = reg >> 8; cmd[3] = reg & 0xFF;
  cmd[4] = 0x00; cmd[5] = count;
  uint16_t crc = calcCRC(cmd, 6);
  cmd[6] = crc & 0xFF; cmd[7] = crc >> 8;

  digitalWrite(dePin, HIGH); delay(5);
  serial.write(cmd, 8); serial.flush();
  delay(5); digitalWrite(dePin, LOW);

  unsigned long t = millis();
  while (serial.available() < (5 + count * 2))
    if (millis() - t > 500) return false;

  uint8_t resp[32];
  serial.readBytes(resp, 5 + count * 2);
  if (resp[0] != addr || resp[1] != 0x03) return false;

  for (int i = 0; i < count; i++)
    out[i] = (resp[3 + i*2] << 8) | resp[4 + i*2];

  return true;
}

// ─── Read NPK ─────────────────────────────────────────
void readNPK() {
  uint16_t data[3];
  // Common register for NPK: 0x001E (N), 0x001F (P), 0x0020 (K)
  // Some sensors use 0x0000 — check your datasheet
  if (rs485Read(NPK_Serial, NPK_DE_RE, 0x01, 0x001E, 3, data)) {
    nitrogen   = data[0];
    phosphorus = data[1];
    potassium  = data[2];
    Serial.printf("NPK: N=%.0f P=%.0f K=%.0f mg/kg\n",
                  nitrogen, phosphorus, potassium);
  } else {
    Serial.println("NPK: READ FAILED");
  }
  delay(100);
}

// ─── Read Moisture ────────────────────────────────────
void readMoisture() {
  uint16_t data[1];
  if (rs485Read(MOIST_Serial, MOIST_DE_RE, 0x01, 0x0000, 1, data)) {
    moisture = data[0] / 10.0;
    Serial.printf("Moisture: %.1f%%\n", moisture);
  } else {
    Serial.println("Moisture: READ FAILED");
  }
  delay(100);
}

// ─── Read EC ──────────────────────────────────────────
void readEC() {
  uint16_t data[1];
  if (rs485Read(EC_Serial, EC_DE_RE, 0x01, 0x0000, 1, data)) {
    ec = data[0] / 1000.0;
    Serial.printf("EC: %.3f mS/cm\n", ec);
  } else {
    Serial.println("EC: READ FAILED");
  }
  delay(100);
}

// ─── Read pH ──────────────────────────────────────────
void readPH() {
  int raw = analogRead(PH_PIN);
  float voltage = raw * (3.3 / 4095.0);
  ph = 7.0 + (2.5 - voltage) * 3.5;
  ph = constrain(ph, 0, 14);
  Serial.printf("pH: %.2f\n", ph);
}

// ─── Read DHT11 ───────────────────────────────────────
void readDHT() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (!isnan(h) && !isnan(t)) {
    humidity = h; temperature = t;
    Serial.printf("Temp: %.1fC  Hum: %.1f%%\n", t, h);
  } else Serial.println("DHT11: READ FAILED");
}

// ─── Read MQ-135 ─────────────────────────────────────
void readMQ135() {
  mq135_val = analogRead(MQ135_AO);
  Serial.printf("MQ135: %d %s\n", mq135_val,
    mq135_val > NH3_ALARM ? "!HIGH NH3!" : "OK");
}

// ─── Read Rain ────────────────────────────────────────
void readRain() {
  rain_val = analogRead(RAIN_AO);
  raining  = (digitalRead(RAIN_DO) == LOW);
  Serial.printf("Rain: %s (raw:%d)\n", raining ? "YES" : "NO", rain_val);
}

// ─── Read Water Level ────────────────────────────────
void readWaterLevel() {
  water_val = analogRead(WATER_LVL);
  Serial.printf("Water Level: %d\n", water_val);
}

// ─── Pump Control ─────────────────────────────────────
void controlPump() {
  bool tankEmpty = (water_val < TANK_EMPTY);
  if (raining || tankEmpty) {
    digitalWrite(RELAY_PIN, HIGH); pump_on = false;
  } else if (moisture < MOISTURE_LOW) {
    digitalWrite(RELAY_PIN, LOW);  pump_on = true;
  } else if (moisture > MOISTURE_HIGH) {
    digitalWrite(RELAY_PIN, HIGH); pump_on = false;
  }
  Serial.printf("Pump: %s\n", pump_on ? "ON" : "OFF");
}

// ─── LCD ──────────────────────────────────────────────
void updateLCD() {
  lcd.clear();
  switch (lcdPage) {
    case 0:
      lcd.setCursor(0,0); lcd.print("=== MITTI SOIL ==");
      lcd.setCursor(0,1);
      lcd.printf("N:%.0f P:%.0f K:%.0f", nitrogen, phosphorus, potassium);
      lcd.setCursor(0,2); lcd.printf("pH: %.1f  EC:%.2f", ph, ec);
      lcd.setCursor(0,3); lcd.printf("Moist: %.1f%%", moisture);
      break;
    case 1:
      lcd.setCursor(0,0); lcd.print("=== ENVIRONMENT =");
      lcd.setCursor(0,1); lcd.printf("Temp: %.1f C", temperature);
      lcd.setCursor(0,2); lcd.printf("Hum:  %.1f%%", humidity);
      lcd.setCursor(0,3);
      lcd.printf("NH3: %s", mq135_val > NH3_ALARM ? "HIGH!" : "OK");
      break;
    case 2:
      lcd.setCursor(0,0); lcd.print("=== IRRIGATION ==");
      lcd.setCursor(0,1);
      lcd.printf("Rain: %s", raining ? "YES" : "NO");
      lcd.setCursor(0,2);
      lcd.printf("Tank: %s", water_val < TANK_EMPTY ? "LOW!" : "OK");
      lcd.setCursor(0,3);
      lcd.printf("Pump: %s", pump_on ? "RUNNING" : "OFF");
      break;
    case 3:
      lcd.setCursor(0,0); lcd.print("=== MITTI v1.0 ==");
      lcd.setCursor(0,1); lcd.print("Samsung SFT 2025");
      lcd.setCursor(0,2); lcd.print("Soil Intelligence");
      lcd.setCursor(0,3); lcd.print("for Bharat's Farms");
      break;
  }
  lcdPage = (lcdPage + 1) % 4;
}

// ─── Send to Server ───────────────────────────────────
void sendToServer() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  String body = "{";
  body += "\"n\":" + String(nitrogen) + ",";
  body += "\"p\":" + String(phosphorus) + ",";
  body += "\"k\":" + String(potassium) + ",";
  body += "\"moisture\":" + String(moisture) + ",";
  body += "\"ec\":" + String(ec) + ",";
  body += "\"ph\":" + String(ph) + ",";
  body += "\"temp\":" + String(temperature) + ",";
  body += "\"humidity\":" + String(humidity) + ",";
  body += "\"mq135\":" + String(mq135_val) + ",";
  body += "\"raining\":" + String(raining ? "true" : "false") + ",";
  body += "\"pump\":" + String(pump_on ? "true" : "false");
  body += "}";
  http.POST(body);
  http.end();
}

// ─── Setup ────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // RS485 serials
  NPK_Serial.begin(9600, SERIAL_8N1, NPK_RX, NPK_TX);
  MOIST_Serial.begin(9600, SERIAL_8N1, MOIST_RX, MOIST_TX);
  EC_Serial.begin(9600);

  // Direction pins
  pinMode(NPK_DE_RE,   OUTPUT); digitalWrite(NPK_DE_RE,   LOW);
  pinMode(MOIST_DE_RE, OUTPUT); digitalWrite(MOIST_DE_RE, LOW);
  pinMode(EC_DE_RE,    OUTPUT); digitalWrite(EC_DE_RE,    LOW);
  pinMode(RELAY_PIN,   OUTPUT); digitalWrite(RELAY_PIN,   HIGH);
  pinMode(RAIN_DO,     INPUT);
  pinMode(MQ135_DO,    INPUT);

  dht.begin();

  Wire.begin(21, 22);
  lcd.init(); lcd.backlight();
  lcd.setCursor(0,0); lcd.print("   MITTI v1.0   ");
  lcd.setCursor(0,1); lcd.print("  Starting up.. ");

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t++ < 20) delay(500);

  lcd.setCursor(0,2);
  lcd.print(WiFi.status() == WL_CONNECTED ? "WiFi: Connected " : "WiFi: Offline  ");
  delay(1500);
  Serial.println("MITTI READY");
}

// ─── Loop ─────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  if (now - lastRead > 5000) {
    lastRead = now;
    readNPK();
    readMoisture();
    readEC();
    readPH();
    readDHT();
    readMQ135();
    readRain();
    readWaterLevel();
    controlPump();
  }

  if (now - lastLCD > 3000) {
    lastLCD = now;
    updateLCD();
  }

  if (now - lastSend > 30000) {
    lastSend = now;
    sendToServer();
  }
}
