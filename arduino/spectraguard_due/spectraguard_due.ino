#include <Wire.h>

const byte ADXL345 = 0x53;
const unsigned long SAMPLE_PERIOD_US = 2500;  // 400 Hz

void writeRegister(byte reg, byte value) {
  Wire.beginTransmission(ADXL345);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

byte readRegister(byte reg) {
  Wire.beginTransmission(ADXL345);
  Wire.write(reg);

  if (Wire.endTransmission() != 0) {
    return 0xFF;
  }

  Wire.requestFrom(ADXL345, (byte)1);

  if (Wire.available() == 1) {
    return Wire.read();
  }

  return 0xFF;
}

void setup() {
  Serial.begin(460800);
  Wire.begin();
  analogReadResolution(12);

  delay(1000);

  // Wait until ADXL345 responds with its correct device ID: 0xE5
  while (readRegister(0x00) != 0xE5) {
    Serial.println("Waiting for ADXL345...");
    delay(250);
  }

  writeRegister(0x31, 0x08);  // full resolution, +/-2 g
  writeRegister(0x2C, 0x0C);  // 400 Hz
  writeRegister(0x2D, 0x08);  // measurement mode

  delay(100);

  Serial.println("t_us,x_g,y_g,z_g,mic");
}

void loop() {
  static unsigned long nextSample = micros();

  if ((long)(micros() - nextSample) >= 0) {
    nextSample += SAMPLE_PERIOD_US;

    Wire.beginTransmission(ADXL345);
    Wire.write(0x32);

    if (Wire.endTransmission(false) != 0)
      return;

    Wire.requestFrom(ADXL345, (byte)6);

    if (Wire.available() == 6) {
      int16_t xRaw = Wire.read() | (Wire.read() << 8);
      int16_t yRaw = Wire.read() | (Wire.read() << 8);
      int16_t zRaw = Wire.read() | (Wire.read() << 8);

      float x = xRaw * 0.0039;
      float y = yRaw * 0.0039;
      float z = zRaw * 0.0039;

      int mic = analogRead(A0);

      Serial.print(micros());
      Serial.print(",");
      Serial.print(x, 4);
      Serial.print(",");
      Serial.print(y, 4);
      Serial.print(",");
      Serial.print(z, 4);
      Serial.print(",");
      Serial.println(mic);
    }
  }
}
