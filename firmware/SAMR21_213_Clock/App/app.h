#ifndef APP_H
#define APP_H
#include "samr21g18a.h"

#define APP_MAGIC 0x45504431UL
#define EPD_WIDTH 104U
#define EPD_HEIGHT 212U
#define EPD_PLANE_BYTES (EPD_WIDTH * EPD_HEIGHT / 8U)
#define APP_STARTUP_COMMAND 8U /* Start the large 24-hour clock. */
#define EPD_OTP_BYTES 4096U
typedef struct {
    uint32_t magic;
    uint32_t stage;           /* 1 boot, 2 init, 3 data, 4 refresh, 5 power-off, 6 idle, 0xe0 error */
    uint32_t error;
    uint32_t ticks_ms;
    uint32_t command;         /* 1 white, 2 black border, 3 white border, 4 pattern, 5 red, 6 demo, 7 OTP read */
    uint32_t completed;
    uint32_t last_epd_command;
    uint32_t busy;
    uint32_t busy_wait_ms;
    uint32_t refresh_ms;
    uint32_t temperature_raw;
    uint32_t border;
    uint32_t bytes_sent;
    uint32_t refresh_mode; /* 0=OTP full, 1=RAM differential */
    uint32_t partial_count;
    uint32_t full_count;
    uint32_t busy_seen;
} AppStatus;
extern volatile AppStatus g_status;
extern volatile uint8_t g_otp_buffer[EPD_OTP_BYTES];
extern uint32_t SystemCoreClock;
void delay_ms(uint32_t ms);
void epd_gpio_init(void);
int epd_display(uint8_t border, uint32_t pattern);
int epd_clock_refresh(uint8_t full_refresh);
int epd_read_otp(void);
void epd_emergency_off(void);
#endif
