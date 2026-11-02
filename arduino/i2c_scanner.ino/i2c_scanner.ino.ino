#include <Wire.h>

void setup() {
  Serial.begin(115200);
  while (!Serial);

  Wire.begin();

  Serial.println("I2C scanner starting...");
}

void loop() {
  byte error, address;
  int devicesFound = 0;

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("Device found at 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      devicesFound++;
    }
  }

  if (devicesFound == 0) {
    Serial.println("No I2C devices found.");
  }

  delay(3000);
}