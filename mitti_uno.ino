/*
 * MITTI — Soil Intelligence System
 * Arduino Uno Version (Offline / Testing)
 * Samsung Solve for Tomorrow 2025
 *
 * Sensors wired:
 *  D2  → MAX485 RO (RS485 RX)
 *  D3  → MAX485 DI (RS485 TX)
 *  D4  → MAX485 DE+RE
 *  D5  → DHT11 Data
 *  D6  → Rain Sensor DO
 *  D7  → Relay IN (pump)
 *  A0  → pH Probe
 *  A1  → MQ-135 AO
 *  A2  → Rain Sensor AO
 *  A3  → Water Level Sensor
 *  A4  → LCD SDA (I2C)
 *  A5  → LCD SCL (I2C)
 */

#include <SoftwareSerial.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

// ─── Pin Definitions ──────────────────────────────────
#define RS485_RX       2
#define RS485_TX       3
#define RS485_DE_RE    4
#define DHT_PIN        5
#define RAIN_DO_PIN    6
#define RELAY_PIN      7
#define PH_PIN         A0
#define MQ135_PIN      A1
#define RAIN_AO_PIN    A2
#define WATER_LVL_PIN  A3

// ─── Thresholds ───────────────────────────────────────
#define MOISTURE_LOW   30      // % — turn pump ON below this
#define MOISTURE_HIGH  70      // % — turn pump OFF above this
#define WATER_LVL_MIN  200     // analog — tank empty below this
#define MQ135_ALARM    600     // analog — ammonia high above this

// ─── Objects ──────────────────────────────────────────
SoftwareSerial RS485(RS485_RX, RS485_TX);
LiquidCrystal_I2C lcd(0x27, 20, 4); // Try 0x3F if blank
DHT dht(DHT_PIN, DHT11);

// ─── Sensor Values ────────────────────────────────────
int   nitrogen    = 0;
int   phosphorus  = 0;
int   potassium   = 0;
float moisture    = 0;
float ec          = 0;
float ph          = 0;
float temperature = 0;
float humidity    = 0;
int   mq135       = 0;
int   rain_raw    = 0;
int   water_level = 0;
bool  is_raining  = false;
bool  pump_on     = false;

int   lcdPage     = 0;
unsigned long lastRead = 0;
unsigned long lastLCD  = 0;

// ─── CRC16 for Modbus ─────────────────────────────────
uint16_t calcCRC(uint8_t* buf, int len) {
  uint16_t crc = 0xFFFF;
  for (int i = 0; i < len; i++) {
    crc ^= buf[i];
    for (int j = 0; j < 8; j++) {
      if (crc & 1) { crc >>= 1; crc ^= 0xA001; }
      else           crc >>= 1;
    }
  }
  return crc;
}

// ─── RS485 Modbus Read ────────────────────────────────
bool rs485Read(uint8_t addr, uint16_t reg, uint8_t count, uint16_t* out) {
  // Flush any leftover bytes
  while (RS485.available()) RS485.read();

  // Build command
  uint8_t cmd[8];
  cmd[0] = addr;
  cmd[1] = 0x03;
  cmd[2] = reg >> 8;
  cmd[3] = reg & 0xFF;
  cmd[4] = 0x00;
  cmd[5] = count;
  uint16_t crc = calcCRC(cmd, 6);
  cmd[6] = crc & 0xFF;
  cmd[7] = crc >> 8;

  // Send
  digitalWrite(RS485_DE_RE, HIGH);
  delay(5);
  RS485.write(cmd, 8);
  RS485.flush();
  delay(5);
  digitalWrite(RS485_DE_RE, LOW);

  // Wait for response
  unsigned long t = millis();
  while (RS485.available() < (5 + count * 2)) {
    if (millis() - t > 500) return false; // timeout
  }

  // Read response
  uint8_t resp[20];
  int n = RS485.readBytes(resp, 5 + count * 2);

  if (resp[0] != addr || resp[1] != 0x03) return false;

  for (int i = 0; i < count; i++) {
    out[i] = (resp[3 + i * 2] << 8) | resp[4 + i * 2];
  }
  return true;
}

// ─── Read NPK (addr 0x01) ─────────────────────────────
void readNPK() {
  uint16_t data[3];
  // Common NPK register: 0x001E (N), 0x001F (P), 0x0020 (K)
  if (rs485Read(0x01, 0x001E, 3, data)) {
    nitrogen   = data[0];
    phosphorus = data[1];
    potassium  = data[2];
    Serial.print(F("NPK OK: N="));
    Serial.print(nitrogen);
    Serial.print(F(" P="));
    Serial.print(phosphorus);
    Serial.print(F(" K="));
    Serial.println(potassium);
  } else {
    Serial.println(F("NPK FAIL"));
  }
  delay(100);
}

// ─── Read Moisture (addr 0x02) ────────────────────────
void readMoisture() {
  uint16_t data[1];
  if (rs485Read(0x02, 0x0000, 1, data)) {
    moisture = data[0] / 10.0;
    Serial.print(F("Moisture: "));
    Serial.print(moisture);
    Serial.println(F("%"));
  } else {
    Serial.println(F("Moisture FAIL"));
  }
  delay(100);
}

// ─── Read EC (addr 0x03) ──────────────────────────────
void readEC() {
  uint16_t data[1];
  if (rs485Read(0x03, 0x0000, 1, data)) {
    ec = data[0] / 1000.0;
    Serial.print(F("EC: "));
    Serial.print(ec, 3);
    Serial.println(F(" mS/cm"));
  } else {
    Serial.println(F("EC FAIL"));
  }
  delay(100);
}

// ─── Read pH ─────────────────────────────────────────
void readPH() {
  int raw = analogRead(PH_PIN);
  // Convert 0-1023 → 0-5V → pH scale
  // Calibrate with pH buffer (4.0, 7.0) for accuracy
  float voltage = raw * (5.0 / 1023.0);
  ph = 7.0 + (2.5 - voltage) * 3.5;
  ph = constrain(ph, 0, 14);
  Serial.print(F("pH: "));
  Serial.println(ph, 1);
}

// ─── Read DHT11 ──────────────────────────────────────
void readDHT() {
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  if (!isnan(h) && !isnan(t)) {
    humidity    = h;
    temperature = t;
    Serial.print(F("Temp: "));
    Serial.print(temperature);
    Serial.print(F("C  Hum: "));
    Serial.print(humidity);
    Serial.println(F("%"));
  } else {
    Serial.println(F("DHT11 FAIL"));
  }
}

// ─── Read MQ-135 ─────────────────────────────────────
void readMQ135() {
  mq135 = analogRead(MQ135_PIN);
  Serial.print(F("MQ135 (NH3/Air): "));
  Serial.print(mq135);
  Serial.println(mq135 > MQ135_ALARM ? F(" !HIGH AMMONIA!") : F(" OK"));
}

// ─── Read Rain ────────────────────────────────────────
void readRain() {
  rain_raw   = analogRead(RAIN_AO_PIN);
  is_raining = (digitalRead(RAIN_DO_PIN) == LOW);
  Serial.print(F("Rain: "));
  Serial.println(is_raining ? F("YES") : F("no"));
}

// ─── Read Water Level ─────────────────────────────────
void readWaterLevel() {
  water_level = analogRead(WATER_LVL_PIN);
  Serial.print(F("Water Level: "));
  Serial.println(water_level);
}

// ─── Pump Control ─────────────────────────────────────
void controlPump() {
  bool tankEmpty = (water_level < WATER_LVL_MIN);

  if (is_raining || tankEmpty) {
    digitalWrite(RELAY_PIN, HIGH); // Relay OFF
    pump_on = false;
  } else if (moisture < MOISTURE_LOW) {
    digitalWrite(RELAY_PIN, LOW);  // Relay ON → pump runs
    pump_on = true;
  } else if (moisture > MOISTURE_HIGH) {
    digitalWrite(RELAY_PIN, HIGH); // Relay OFF
    pump_on = false;
  }
  Serial.print(F("Pump: "));
  Serial.println(pump_on ? F("ON") : F("OFF"));
}

// ─── LCD Display ─────────────────────────────────────
void updateLCD() {
  lcd.clear();
  switch (lcdPage) {

    case 0: // NPK
      lcd.setCursor(0,0); lcd.print(F("=== MITTI SOIL =="));
      lcd.setCursor(0,1);
      lcd.print(F("N:")); lcd.print(nitrogen);
      lcd.print(F(" P:")); lcd.print(phosphorus);
      lcd.print(F(" K:")); lcd.print(potassium);
      lcd.setCursor(0,2); lcd.print(F("mg/kg each"));
      lcd.setCursor(0,3);
      lcd.print(F("pH:")); lcd.print(ph,1);
      lcd.print(F("  EC:")); lcd.print(ec,2);
      break;

    case 1: // Moisture + Pump
      lcd.setCursor(0,0); lcd.print(F("=== MOISTURE ===="));
      lcd.setCursor(0,1);
      lcd.print(F("Soil: ")); lcd.print(moisture,1); lcd.print(F("%"));
      lcd.setCursor(0,2);
      lcd.print(F("Tank: "));
      lcd.print(water_level < WATER_LVL_MIN ? F("LOW!") : F("OK  "));
      lcd.setCursor(0,3);
      lcd.print(F("Pump: "));
      lcd.print(pump_on ? F("RUNNING") : F("OFF    "));
      break;

    case 2: // Ambient + Air
      lcd.setCursor(0,0); lcd.print(F("=== ENVIRONMENT ="));
      lcd.setCursor(0,1);
      lcd.print(F("Temp: ")); lcd.print(temperature,1); lcd.print(F("C"));
      lcd.setCursor(0,2);
      lcd.print(F("Hum:  ")); lcd.print(humidity,1); lcd.print(F("%"));
      lcd.setCursor(0,3);
      lcd.print(F("NH3:  "));
      lcd.print(mq135 > MQ135_ALARM ? F("HIGH!") : F("OK   "));
      break;

    case 3: // Status
      lcd.setCursor(0,0); lcd.print(F("=== STATUS ======"));
      lcd.setCursor(0,1);
      lcd.print(F("Rain: "));
      lcd.print(is_raining ? F("YES") : F("NO "));
      lcd.setCursor(0,2);
      lcd.print(F("MQ135: ")); lcd.print(mq135);
      lcd.setCursor(0,3);
      lcd.print(F("MITTI v1.0 | UNO"));
      break;
  }
  lcdPage = (lcdPage + 1) % 4;
}

// ─── Setup ────────────────────────────────────────────
void setup() {
  Serial.begin(9600);
  Serial.println(F("=== MITTI UNO BOOT ==="));

  pinMode(RS485_DE_RE, OUTPUT);
  pinMode(RELAY_PIN,   OUTPUT);
  pinMode(RAIN_DO_PIN, INPUT);
  digitalWrite(RS485_DE_RE, LOW);  // Receive mode
  digitalWrite(RELAY_PIN,   HIGH); // Pump OFF

  RS485.begin(9600);
  dht.begin();

  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0,0); lcd.print(F("   MITTI v1.0   "));
  lcd.setCursor(0,1); lcd.print(F(" Soil Intelligence"));
  lcd.setCursor(0,2); lcd.print(F("  Arduino  Uno   "));
  lcd.setCursor(0,3); lcd.print(F("  Booting...     "));
  delay(2000);
  Serial.println(F("=== READY ==="));
}

// ─── Loop ─────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // Read all sensors every 5 seconds
  if (now - lastRead > 5000) {
    lastRead = now;
    Serial.println(F("--- Sensor Read ---"));
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

  // Update LCD every 3 seconds
  if (now - lastLCD > 3000) {
    lastLCD = now;
    updateLCD();
  }
}
