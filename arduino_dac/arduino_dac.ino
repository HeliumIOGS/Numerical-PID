int analogPin = 8;
int zeroV = 1;
int threeV = 231;

void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);
  // initialize DAC:
  analogWrite(DAC1,0);
  // initialize A_O:
  pinMode(analogPin, OUTPUT);
}

void loop() {
  // Supply LED voltage:
  dacc_set_channel_selection(DACC_INTERFACE, 1);
  dacc_write_conversion_data(DACC_INTERFACE, 4095);
  // Enable relay:
  analogWrite(analogPin, threeV); delay(2000);
  analogWrite(analogPin, zeroV); delay(500);
}
