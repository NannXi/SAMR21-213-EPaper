#ifndef DEVICE_CLOCK_H
#define DEVICE_CLOCK_H
#include "app.h"
#define CLOCK_FULL_EVERY_MINUTE 0U
#define CLOCK_PARTIAL_PERIODIC_FULL 1U
extern volatile uint32_t g_clock_enabled,g_clock_policy,g_clock_full_hours;
extern volatile uint32_t g_clock_sync_tick,g_clock_sync_second,g_clock_last_minute,g_clock_last_full_tick;
int device_clock_valid(const uint8_t *payload);
void device_clock_configure(const uint8_t *payload);
void device_clock_stop(void);
uint32_t device_clock_seconds(void);
int device_clock_draw(uint8_t full);
void device_clock_poll(void);
#endif
