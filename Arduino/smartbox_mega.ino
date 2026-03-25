/*
 * SMARTBOX - Boite aux Lettres Connectee & Securisee
 * Code Arduino Mega 2560 - Version 2.0
 * 
 * PROTOCOLE SERIE (USB vers Raspberry Pi):
 * Pi -> Arduino : "CODE:XXXX", "REVOKE"
 * Arduino -> Pi : "MAIL_DETECTED", "MAIL_CLEARED", "CODE_OK",
 *                 "CODE_FAIL", "DOOR_OPENED", "DOOR_CLOSED",
 *                 "PARCEL_DETECTED", "PARCEL_NONE"
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Keypad.h>
#include <Servo.h>

// ===================== PINS ARDUINO MEGA =====================
// LCD I2C : SDA = pin 20, SCL = pin 21
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Keypad 4x4
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'D', '#', '0', '*'},
  {'C', '9', '8', '7'},
  {'B', '6', '5', '4'},
  {'A', '3', '2', '1'}
};
byte rowPins[ROWS] = {28, 26, 24, 22};
byte colPins[COLS] = {36, 34, 32, 30};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// Servo
const int SERVO_PIN = 9;
Servo servo;
const int SERVO_LOCKED = 0;
const int SERVO_UNLOCKED = 90;

// LEDs & Buzzer
const int LED_GREEN = 10;
const int LED_RED = 11;
const int BUZZER = 12;

// Capteurs
const int LDR_PIN = A0;
const int LDR_SEUIL = 50;
const int TRIG_PIN = 3;
const int ECHO_PIN = 4;
const int PARCEL_SEUIL = 20;
const int REED_PIN = 2;
const int BUTTON_MAIL_PIN = 5;

// ===================== VARIABLES =====================
String activeCode = "";
bool codeActive = false;
String inputCode = "";
const int CODE_LENGTH = 4;

bool doorOpen = false;
bool doorLocked = true;
bool mailPresent = false;
bool parcelPresent = false;
bool ultrasonicActive = true;

unsigned long lastMailCheck = 0;
unsigned long lastButtonCheck = 0;
unsigned long lastDoorCheck = 0;
const int DEBOUNCE_DELAY = 200;

bool lastDoorState = false;
bool lastMailState = false;

// Timeout servo
unsigned long unlockTime = 0;
const unsigned long UNLOCK_TIMEOUT = 30000;  // 30 secondes
bool waitingForDoor = false;

// Timeout saisie code
unsigned long lastKeyTime = 0;
const unsigned long INPUT_TIMEOUT = 15000;  // 15 secondes

// ===================== SETUP =====================
void setup() {
  Serial.begin(9600);
  
  lcd.init();
  lcd.backlight();
  displayWelcome();
  
  servo.attach(SERVO_PIN);
  lockDoor();
  
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, HIGH);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(REED_PIN, INPUT_PULLUP);
  pinMode(BUTTON_MAIL_PIN, INPUT_PULLUP);
  
  setLEDs(false, true);
  beepStartup();

  Serial.println("SMARTBOX_READY");
}

// ===================== LOOP =====================
void loop() {
  handleSerialInput();
  handleKeypad();
  handleInputTimeout();
  handleDoorSensor();
  handleMailSensor();
  handleMailButton();
  delay(10);
}

// ===================== COMMUNICATION SERIE =====================
void handleSerialInput() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("CODE:")) {
      activeCode = command.substring(5);
      codeActive = true;
      Serial.println("CODE_RECEIVED");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Code actif");
      lcd.setCursor(0, 1);
      lcd.print("Tapez le code:");
      delay(1000);
      displayEnterCode();
    } else if (command == "REVOKE") {
      activeCode = "";
      codeActive = false;
      inputCode = "";
      Serial.println("CODE_REVOKED");
      displayWelcome();
    }
  }
}

void sendToPi(String message) {
  Serial.println(message);
}

// ===================== KEYPAD =====================
void handleKeypad() {
  char key = keypad.getKey();
  
  if (key) {
    beepKey();
    lastKeyTime = millis();  // Reset le timeout
    
    if (key == '*') {
      inputCode = "";
      displayEnterCode();
    } else if (key == '#') {
      if (inputCode.length() == CODE_LENGTH) {
        checkCode();
      } else {
        beepError();
        lcd.setCursor(0, 1);
        lcd.print("Code incomplet! ");
        delay(1000);
        displayEnterCode();
      }
    } else if (key >= '0' && key <= '9') {
      if (inputCode.length() < CODE_LENGTH) {
        inputCode += key;
        displayCodeInput();
      }
    }
  }
}

// ===================== TIMEOUT SAISIE CODE =====================
void handleInputTimeout() {
  // Si on a commencé à taper et pas de touche depuis 15 sec
  if (inputCode.length() > 0 && (millis() - lastKeyTime > INPUT_TIMEOUT)) {
    inputCode = "";
    beepError();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Temps ecoule!");
    delay(1500);
    displayWelcome();
  }
}

void displayCodeInput() {
  lcd.setCursor(0, 1);
  lcd.print("Code: ");
  for (unsigned int i = 0; i < inputCode.length(); i++) lcd.print("*");
  for (unsigned int i = inputCode.length(); i < CODE_LENGTH; i++) lcd.print("_");
  lcd.print("      ");
}

void checkCode() {
  if (!codeActive) {
    beepError();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Aucun code");
    lcd.setCursor(0, 1);
    lcd.print("actif!");
    sendToPi("CODE_FAIL");
    setLEDs(false, true);
    delay(2000);
    displayWelcome();
    inputCode = "";
    return;
  }
  
  if (inputCode == activeCode) {
    beepSuccess();
    sendToPi("CODE_OK");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Acces autorise!");
    lcd.setCursor(0, 1);
    lcd.print("Ouvrez la porte");
    setLEDs(true, false);
    unlockDoor();
    
    // Démarre le timeout
    unlockTime = millis();
    waitingForDoor = true;
    
  } else {
    beepError();
    sendToPi("CODE_FAIL");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Code invalide!");
    lcd.setCursor(0, 1);
    lcd.print("Reessayez");
    setLEDs(false, true);
    delay(2000);
    displayEnterCode();
  }
  inputCode = "";
}

// ===================== SERVO =====================
void lockDoor() {
  servo.write(SERVO_LOCKED);
  doorLocked = true;
  setLEDs(false, true);
}

void unlockDoor() {
  servo.write(SERVO_UNLOCKED);
  doorLocked = false;
  setLEDs(true, false);
}

// ===================== REED SWITCH =====================
void handleDoorSensor() {
  if (millis() - lastDoorCheck < DEBOUNCE_DELAY) return;
  lastDoorCheck = millis();
  
  bool currentDoorOpen = (digitalRead(REED_PIN) == HIGH);
  
  // Timeout si porte pas ouverte après 30 sec
  if (waitingForDoor && !doorOpen && (millis() - unlockTime > UNLOCK_TIMEOUT)) {
    waitingForDoor = false;
    lockDoor();
    beepError();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Temps ecoule!");
    lcd.setCursor(0, 1);
    lcd.print("Reverrouillage..");
    delay(2000);
    displayWelcome();
    return;
  }
  
  if (currentDoorOpen != lastDoorState) {
    lastDoorState = currentDoorOpen;
    
    if (currentDoorOpen && !doorOpen) {
      doorOpen = true;
      waitingForDoor = false;  // Plus besoin du timeout
      ultrasonicActive = false;
      sendToPi("DOOR_OPENED");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Porte ouverte");
      delay(1500);
      lcd.setCursor(0, 1);
      lcd.print("Deposez colis...");
    } else if (!currentDoorOpen && doorOpen) {
      doorOpen = false;
      sendToPi("DOOR_CLOSED");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Porte fermee");
      lcd.setCursor(0, 1);
      lcd.print("Verrouillage...");
      delay(1500);
      lockDoor();
      beepLock();
      ultrasonicActive = true;
      delay(500);
      scanParcel();
      delay(2000);
      displayWelcome();
    }
  }
}

// ===================== HC-SR04 =====================
long measureDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  long distance = duration * 0.034 / 2;
  if (distance == 0) distance = 999;
  return distance;
}

void scanParcel() {
  if (!ultrasonicActive) return;
  long totalDist = 0;
  for (int i = 0; i < 5; i++) {
    totalDist += measureDistance();
    delay(50);
  }
  long avgDist = totalDist / 5;
  
  if (avgDist < PARCEL_SEUIL) {
    parcelPresent = true;
    sendToPi("PARCEL_DETECTED");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Colis securise!");
    lcd.setCursor(0, 1);
    lcd.print("Merci :)");
    beepSuccess();
    delay(3000);
  } else {
    parcelPresent = false;
    sendToPi("PARCEL_NONE");
  }
}


// ===================== LASER + LDR =====================
void handleMailSensor() {
  if (millis() - lastMailCheck < DEBOUNCE_DELAY) return;
  lastMailCheck = millis();
  
  int ldrValue = analogRead(LDR_PIN);
  bool mailDetected = (ldrValue > LDR_SEUIL);
  
  if (mailDetected && !lastMailState) {
    mailPresent = true;
    lastMailState = true;
    sendToPi("MAIL_DETECTED");
    beepMail();
    
    // Affiche seulement si pas en mode porte ET pas en train de taper un code
    if (!doorOpen && !waitingForDoor && inputCode.length() == 0) {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Courrier recu!");
      delay(3000);
      displayWelcome();
    }
  } else if (!mailDetected) {
    lastMailState = false;
  }
}

// ===================== BOUTON COURRIER =====================
void handleMailButton() {
  if (millis() - lastButtonCheck < DEBOUNCE_DELAY) return;
  lastButtonCheck = millis();
  
  if (digitalRead(BUTTON_MAIL_PIN) == LOW) {
    if (mailPresent) {
      mailPresent = false;
      sendToPi("MAIL_CLEARED");
      beepKey();
      
      // Affiche seulement si pas en mode porte ET pas en train de taper un code
      if (!doorOpen && !waitingForDoor && inputCode.length() == 0) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Courrier");
        lcd.setCursor(0, 1);
        lcd.print("recupere!");
        delay(1500);
        displayWelcome();
      }
    }
    delay(300);
  }
}

// ===================== AFFICHAGE LCD =====================
void displayWelcome() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SmartBox v2.0");
  lcd.setCursor(0, 1);
  if (codeActive) lcd.print("Tapez le code:");
  else lcd.print("En attente...");
}

void displayEnterCode() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Entrez le code:");
  lcd.setCursor(0, 1);
  lcd.print("Code: ____      ");
}

// ===================== LEDs =====================
void setLEDs(bool green, bool red) {
  digitalWrite(LED_GREEN, green ? HIGH : LOW);
  digitalWrite(LED_RED, red ? HIGH : LOW);
}

// ===================== BUZZER (ACTIF INVERSE) =====================
void beepKey() { 
  digitalWrite(BUZZER, LOW);
  delay(50);
  digitalWrite(BUZZER, HIGH);
}

void beepSuccess() { 
  digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH);
  delay(100);
  digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH);
}

void beepError() { 
  digitalWrite(BUZZER, LOW);
  delay(500);
  digitalWrite(BUZZER, HIGH);
}

void beepLock() { 
  digitalWrite(BUZZER, LOW);
  delay(150);
  digitalWrite(BUZZER, HIGH);
}

void beepMail() { 
  digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH);
}

void beepStartup() {
  digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH);
  delay(120);
  digitalWrite(BUZZER, LOW);
  delay(100);
  digitalWrite(BUZZER, HIGH);
  delay(120);
  digitalWrite(BUZZER, LOW);
  delay(150);
  digitalWrite(BUZZER, HIGH);
}
