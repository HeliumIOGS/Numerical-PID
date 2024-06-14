#include <SPI.h>
#include <Ethernet.h>

const int relay_pin_dac0 = 2;
const int relay_pin_dac1 = 3;
const int relay_open = 0;
const int relay_close = 255;
int msg[4];

// network configuration.  gateway and subnet are optional.

 // the media access control (ethernet hardware) address for the shield:
byte mac[] = { 0xA8, 0x61, 0x0A, 0xAE, 0x01, 0x88 };
//the IP address for the shield:
byte ip[] = { 10, 118, 16, 29 };
// the router's gateway address:
byte gateway[] = { 192, 168, 0, 2};
// the subnet:
byte subnet[] = { 255, 255, 255, 0 };

// telnet defaults to port 23
EthernetServer server = EthernetServer(7777);

void setup()
{
  analogWrite(DAC0,2047);
  analogWrite(DAC1,2047);
  pinMode(relay_pin_dac0,OUTPUT);
  pinMode(relay_pin_dac1,OUTPUT);
  analogWrite(relay_pin_dac0, relay_open);
  analogWrite(relay_pin_dac1, relay_open);
  
  // initialize the ethernet device:
  Ethernet.begin(mac, ip, gateway, subnet);
  // start listening for clients:
  server.begin();
}

void loop()
{
  // if an incoming client connects, there will be bytes available to read:
  EthernetClient client = server.available();
  if (client) {
    int i ;
    int number_of_bytes = 4;
  for(i=0;i<number_of_bytes;i++){
    msg[i] = client.read();
  }

  int channel = msg[0];
  int voltage = msg[1] + pow(2,8)*msg[2];
  bool output = msg[3];

  dacc_set_channel_selection(DACC_INTERFACE, channel);
  dacc_write_conversion_data(DACC_INTERFACE, voltage);
  analogWrite(2+channel, output*255);
    
  }
}
