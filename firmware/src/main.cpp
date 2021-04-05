#include <Arduino.h>

class TLC6C5748x3 {
public:

  struct Channel {
    uint16_t pwm_r;
    uint16_t pwm_g;
    uint16_t pwm_b;
    uint8_t dc_r;
    uint8_t dc_g;
    uint8_t dc_b;
    bool open_r;
    bool open_g;
    bool open_b;
    bool short_r;
    bool short_g;
    bool short_b;
  };

  struct Data {
    Channel ch[16];
    uint8_t mc_r;
    uint8_t mc_g;
    uint8_t mc_b;
    uint8_t bc_r;
    uint8_t bc_g;
    uint8_t bc_b;
    bool dsprpt;
    bool tmgrst;
    bool rfresh;
    bool espwm;
    bool lsdvlt;
  };

  Data data[3];

  inline bool shift_bit(bool d = false) {
    digitalWrite(0, d);
    //delayMicroseconds(1);
    digitalWrite(20, HIGH);
    //delayMicroseconds(1);
    digitalWrite(20, LOW);
    //delayMicroseconds(1);
    return digitalRead(1);
  }
  
  inline void shift_word(uint16_t d, uint8_t nb) {
    for (int8_t i = nb - 1; i >= 0; i--) {
      shift_bit(d & (1 << i));
    }
  }
  
  void update() {
    // MSB of third device first!

    //delayMicroseconds(10);
    
    // Send control data while reading fault data from previous cycle.
    digitalWrite(6, LOW);
    //delayMicroseconds(50);
    for (int8_t device = 2; device >= 0; device--) {
      Data &d = data[device];
      d.ch[15].open_b = shift_bit(true);  // write 768 (select control latch), read 767
      d.ch[15].open_g = shift_bit(true);  // write 767 (control data write command in next 8 bits, 0x96), read 766
      d.ch[15].open_r = shift_bit(false); // write 766, read 765
      d.ch[14].open_b = shift_bit(false); // write 765, read 764
      d.ch[14].open_g = shift_bit(true);  // write 764, read 763
      d.ch[14].open_r = shift_bit(false); // write 763, read 762
      d.ch[13].open_b = shift_bit(true);  // write 762, read 761
      d.ch[13].open_g = shift_bit(true);  // write 761, read 760
      d.ch[13].open_r = shift_bit(false); // write 760, read 759
      // next shift is write 759, read 758
      for (int8_t channel = 12; channel >= 0; channel--) {
        Channel &c = d.ch[channel];
        c.open_b = shift_bit();
        c.open_g = shift_bit();
        c.open_r = shift_bit();
      }
      // next shift is write 720, read 719
      for (int8_t channel = 15; channel >= 0; channel--) {
        Channel &c = d.ch[channel];
        c.short_b = shift_bit();
        c.short_g = shift_bit();
        c.short_r = shift_bit();
      }
      // next shift is write 672, (read 671)
      for (uint16_t i = 0; i < 302; i++) {
        shift_bit();
      }
      // next shift is write 370
      shift_bit(d.lsdvlt);
      shift_bit(d.espwm);
      shift_bit(d.rfresh);
      shift_bit(d.tmgrst);
      shift_bit(d.dsprpt);
      // next shift is write 365
      shift_word(d.bc_b, 7);
      shift_word(d.bc_g, 7);
      shift_word(d.bc_r, 7);
      // next shift is write 344
      shift_word(d.mc_b, 3);
      shift_word(d.mc_g, 3);
      shift_word(d.mc_r, 3);
      // next shift is write 335
      for (int8_t channel = 15; channel >= 0; channel--) {
        const Channel &c = d.ch[channel];
        shift_word(c.dc_b, 7);
        shift_word(c.dc_g, 7);
        shift_word(c.dc_r, 7);
      }
      // full shift complete
    }
    //delayMicroseconds(10);
    digitalWrite(6, HIGH);

    /*// Read fault data from previous cycle.
    digitalWrite(6, LOW);
    delayMicroseconds(10);
    for (int8_t device = 2; device >= 0; device--) {
      Data &d = data[device];
      // next shift is write 768, read 767
      for (int8_t channel = 15; channel >= 0; channel--) {
        Channel &c = d.ch[channel];
        c.open_b = shift_bit();
        c.open_g = shift_bit();
        c.open_r = shift_bit();
      }
      // next shift is write 720, read 719
      for (int8_t channel = 15; channel >= 0; channel--) {
        Channel &c = d.ch[channel];
        c.short_b = shift_bit();
        c.short_g = shift_bit();
        c.short_r = shift_bit();
      }
      // next shift is write 672, (read 671)
      for (uint16_t i = 0; i < 373; i++) {
        shift_bit();
      }
      // full shift complete
    }

    // Send control data.
    for (int8_t device = 2; device >= 0; device--) {
      Data &d = data[device];
      shift_bit(true);  // write 768 (select control latch)
      shift_bit(true);  // write 767 (control data write command in next 8 bits, 0x96)
      shift_bit(false); // write 766
      shift_bit(false); // write 765
      shift_bit(true);  // write 764
      shift_bit(false); // write 763
      shift_bit(true);  // write 762
      shift_bit(true);  // write 761
      shift_bit(false); // write 760
      // next shift is write 759, read 758
      for (uint16_t i = 0; i < 389; i++) {
        shift_bit();
      }
      // next shift is write 370
      shift_bit(d.lsdvlt);
      shift_bit(d.espwm);
      shift_bit(d.rfresh);
      shift_bit(d.tmgrst);
      shift_bit(d.dsprpt);
      // next shift is write 365
      shift_word(d.bc_b, 7);
      shift_word(d.bc_g, 7);
      shift_word(d.bc_r, 7);
      // next shift is write 344
      shift_word(d.mc_b, 3);
      shift_word(d.mc_g, 3);
      shift_word(d.mc_r, 3);
      // next shift is write 335
      for (int8_t channel = 15; channel >= 0; channel--) {
        const Channel &c = d.ch[channel];
        shift_word(c.dc_b, 7);
        shift_word(c.dc_g, 7);
        shift_word(c.dc_r, 7);
      }
      // full shift complete
    }
    delayMicroseconds(10);
    digitalWrite(6, HIGH);*/

    //delayMicroseconds(10);

    // Send grayscale data.
    digitalWrite(6, LOW);
    //delayMicroseconds(2);
    for (int8_t device = 2; device >= 0; device--) {
      Data &d = data[device];
      shift_bit(false);
      for (int8_t channel = 15; channel >= 0; channel--) {
        const Channel &c = d.ch[channel];
        shift_word(c.pwm_b, 16);
        shift_word(c.pwm_g, 16);
        shift_word(c.pwm_r, 16);
      }
    }
    //delayMicroseconds(10);
    digitalWrite(6, HIGH);
    
  }


};

TLC6C5748x3 led_ctrl;

void setup() {
  Serial.begin(115200);
  pinMode(0, OUTPUT);   // LED driver SIN
  pinMode(1, INPUT);    // LED driver SOUT
  pinMode(2, INPUT);    // minutes Isw
  pinMode(3, INPUT);    // 50Hz override/readout
  pinMode(4, INPUT);    // GPS PPS
  pinMode(5, OUTPUT);   // minutes Ien
  digitalWrite(5, HIGH);
  pinMode(6, OUTPUT);   // LED driver LAT
  pinMode(7, INPUT);    // GPS RX
  pinMode(8, OUTPUT);   // GPS TX
  digitalWrite(8, HIGH);
  pinMode(9, OUTPUT);   // minutes Inc
  digitalWrite(9, HIGH);
  pinMode(10, OUTPUT);  // I/O CS
  digitalWrite(10, HIGH);
  pinMode(11, OUTPUT);  // I/O MOSI
  digitalWrite(11, LOW);
  pinMode(12, INPUT);   // I/O MISO
  pinMode(13, OUTPUT);  // display override
  digitalWrite(13, LOW);
  pinMode(14, OUTPUT);  // I/O SCK
  digitalWrite(14, LOW);
  pinMode(15, INPUT);   // I/O IRQ
  pinMode(16, OUTPUT);  // synchroscope PWM A
  digitalWrite(16, LOW);
  pinMode(17, OUTPUT);  // synchroscope PWM B
  digitalWrite(17, LOW);
  pinMode(18, OUTPUT);  // hours Inc
  digitalWrite(18, HIGH);
  pinMode(19, INPUT);   // hours Isw
  pinMode(20, OUTPUT);  // LED driver SCLK
  pinMode(21, OUTPUT);  // hours Ien
  digitalWrite(21, HIGH);
  pinMode(22, INPUT);   // power Imon
  pinMode(23, INPUT);   // power good
  pinMode(26, OUTPUT);  // minutes/hours Ren
  digitalWrite(26, HIGH);
  for (uint8_t dev = 0; dev < 3; dev++) {
    led_ctrl.data[dev].mc_r = 1;
    led_ctrl.data[dev].mc_g = 1;
    led_ctrl.data[dev].mc_b = 1;
    led_ctrl.data[dev].bc_r = 0x7F;
    led_ctrl.data[dev].bc_g = 0x7F;
    led_ctrl.data[dev].bc_b = 0x7F;
    led_ctrl.data[dev].dsprpt = true;
    led_ctrl.data[dev].tmgrst = false;
    led_ctrl.data[dev].rfresh = false;
    led_ctrl.data[dev].espwm = true;
    led_ctrl.data[dev].lsdvlt = false;
    for (uint8_t ch = 0; ch < 16; ch++) {
      led_ctrl.data[dev].ch[ch].pwm_r = 0x4000;
      led_ctrl.data[dev].ch[ch].pwm_g = 0x0800;
      led_ctrl.data[dev].ch[ch].pwm_b = 0x0000;
      led_ctrl.data[dev].ch[ch].dc_r = 0x0F;
      led_ctrl.data[dev].ch[ch].dc_g = 0x0F;
      led_ctrl.data[dev].ch[ch].dc_b = 0x0F;
    }
  }
  led_ctrl.data[1].ch[13].pwm_r = 0xFFFF;
  led_ctrl.data[1].ch[13].pwm_g = 0xFFFF;
  led_ctrl.data[1].ch[13].pwm_b = 0x8000;
  led_ctrl.data[1].ch[13].dc_r = 0x1F;
  led_ctrl.data[1].ch[13].dc_g = 0x1F;
  led_ctrl.data[1].ch[13].dc_b = 0x10;
  led_ctrl.data[1].ch[14].pwm_r = 0x0000;
  led_ctrl.data[1].ch[14].pwm_g = 0x0000;
  led_ctrl.data[1].ch[14].pwm_b = 0x0000;
}

void loop() {
  // put your main code here, to run repeatedly:
  unsigned long x = micros();
  led_ctrl.update();
  unsigned long y = micros();
  Serial.printf("micros: %lu\n", y - x);
  delay(1000);
}
