void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600);
  // initialize DAC:
  analogWrite(DAC1,0);
}

void loop() {
  // Set voltage:
  dacc_set_channel_selection(DACC_INTERFACE, 1);
  dacc_write_conversion_data(DACC_INTERFACE, 4095);
}
