/* Local wall-clock set by phone; no oscillator calibration or persistence. */
#include "device_clock.h"
#include "graphics.h"
#include "protocol.h"
#include "nfc.h"
volatile uint32_t g_clock_enabled,g_clock_policy,g_clock_full_hours=1U;
volatile uint32_t g_clock_sleep_start=0U,g_clock_sleep_end=360U,g_clock_sleeping=0U;
volatile uint32_t g_clock_sync_tick,g_clock_sync_second,g_clock_last_minute=0xffffffffU,g_clock_last_full_tick;
extern volatile uint32_t g_force_clock_redraw;
static uint32_t u32(const uint8_t *p) { return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24); }
int device_clock_in_sleep(uint32_t seconds) {
    uint32_t start=g_clock_sleep_start*60U,end=g_clock_sleep_end*60U;
    if(start==end)return 0;
    return start<end ? (seconds>=start && seconds<end) : (seconds>=start || seconds<end);
}
int device_clock_valid(const uint8_t *p) {
    int32_t zone=(int16_t)((uint16_t)p[8]|((uint16_t)p[9]<<8));
    uint32_t ms=(uint32_t)p[10]|((uint32_t)p[11]<<8);
    uint32_t sleep_start=(uint32_t)p[12]|((uint32_t)p[13]<<8),sleep_end=(uint32_t)p[14]|((uint32_t)p[15]<<8);
    return p[0]==1U && p[1]<=1U && p[2]>=1U && p[2]<=24U && p[3]==0U && zone>=-840 && zone<=840 && ms<1000U && sleep_start<1440U && sleep_end<1440U && u32(p+16)==0U;
}
void device_clock_configure(const uint8_t *p) {
    int32_t zone=(int16_t)((uint16_t)p[8]|((uint16_t)p[9]<<8));
    int32_t local=(int32_t)(u32(p+4)%86400U)+zone*60;
    uint32_t ms=(uint32_t)p[10]|((uint32_t)p[11]<<8);
    if(local<0) local+=86400; if(local>=86400) local-=86400;
    g_clock_sync_second=(uint32_t)local; g_clock_sync_tick=g_status.ticks_ms-ms;
    g_clock_policy=p[1];g_clock_full_hours=p[2];
    g_clock_sleep_start=(uint32_t)p[12]|((uint32_t)p[13]<<8);
    g_clock_sleep_end=(uint32_t)p[14]|((uint32_t)p[15]<<8);
    g_clock_last_minute=0xffffffffU;g_clock_sleeping=0U;g_clock_enabled=1U;
}
void device_clock_stop(void) {g_clock_enabled=0U;}
uint32_t device_clock_seconds(void) {
    return (g_clock_sync_second+(uint32_t)(g_status.ticks_ms-g_clock_sync_tick)/1000U)%86400U;
}
int device_clock_draw(uint8_t full) {
    uint32_t seconds=device_clock_seconds();
    if(device_clock_in_sleep(seconds)) gfx_sleep();
    else gfx_clock((uint8_t)(seconds/3600U),(uint8_t)((seconds/60U)%60U));
    g_clock_sleeping=device_clock_in_sleep(seconds);
    if(!epd_clock_refresh(full))return 0;
    if(full) {
        g_clock_last_full_tick=g_status.ticks_ms;
        if(g_clock_policy==CLOCK_PARTIAL_PERIODIC_FULL) {
            g_force_clock_redraw=1U;
            if(!epd_clock_refresh(0)) {g_force_clock_redraw=0U;return 0;}
            g_force_clock_redraw=0U;
        }
    }
    g_clock_last_minute=seconds/60U;return 1;
}
void device_clock_poll(void) {
    uint32_t seconds,elapsed;
    uint8_t full;
    if(!g_clock_enabled||g_status.command||g_status.stage!=6U||protocol_busy())return;
    /* Yield to the phone while an RF transaction is present. */
    if(g_nfc.ns_reg&1U)return;
    seconds=device_clock_seconds();
    if(device_clock_in_sleep(seconds) && g_clock_sleeping) {
        g_clock_last_minute=seconds/60U;
        return;
    }
    if(seconds/60U==g_clock_last_minute && device_clock_in_sleep(seconds)==g_clock_sleeping)return;
    elapsed=(uint32_t)(g_status.ticks_ms-g_clock_last_full_tick);
    full=(uint8_t)(device_clock_in_sleep(seconds)!=g_clock_sleeping || g_clock_policy==CLOCK_FULL_EVERY_MINUTE || elapsed>=g_clock_full_hours*3600000U);
    protocol_display_started();
    if(device_clock_draw(full))protocol_display_complete(1);else {g_clock_enabled=0;protocol_display_complete(0);}
    /* Keep unsigned elapsed math bounded across the SysTick wrap. */
    if((uint32_t)(g_status.ticks_ms-g_clock_sync_tick)>=86400000U) {
        seconds=device_clock_seconds();g_clock_sync_second=seconds;g_clock_sync_tick=g_status.ticks_ms-((uint32_t)(g_status.ticks_ms-g_clock_sync_tick)%1000U);
    }
}

uint32_t device_clock_next_wakeup_ms(void) {
    uint32_t seconds=device_clock_seconds();
    uint32_t ms=(uint32_t)(g_status.ticks_ms-g_clock_sync_tick)%1000U;
    uint32_t next=(60U-(seconds%60U))*1000U-ms;
    return next<100U ? 100U : next;
}
