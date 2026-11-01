#include <Wire.h>

const byte ADXL345 = 0x53;
const unsigned long SAMPLE_PERIOD_US = 2500;  // 400 Hz

void writeRegister(byte reg, byte value) {
  Wire.beginTransmission(ADXL345);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(460800);
  while (!Serial);

  Wire.begin();

  // Full resolution, +/-2 g
  writeRegister(0x31, 0x08);

  // Output data rate = 400 Hz
  writeRegister(0x2C, 0x0C);

  // Measurement mode
  writeRegister(0x2D, 0x08);

  Serial.println("t_us,x_g,y_g,z_g");
}

void loop() {
  static unsigned long nextSample = micros();

  if ((long)(micros() - nextSample) >= 0) {
    nextSample += SAMPLE_PERIOD_US;

    Wire.beginTransmission(ADXL345);
    Wire.write(0x32);
    Wire.endTransmission(false);

    Wire.requestFrom(ADXL345, (byte)6);

    if (Wire.available() == 6) {
      int16_t xRaw = Wire.read() | (Wire.read() << 8);
      int16_t yRaw = Wire.read() | (Wire.read() << 8);
      int16_t zRaw = Wire.read() | (Wire.read() << 8);

      float x = xRaw * 0.0039;
      float y = yRaw * 0.0039;
      float z = zRaw * 0.0039;

      Serial.print(micros());
      Serial.print(",");
      Serial.print(x, 4);
      Serial.print(",");
      Serial.print(y, 4);
      Serial.print(",");
      Serial.println(z, 4);
    }
  }
}