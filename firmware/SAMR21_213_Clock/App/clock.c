#include "app.h"
#include "graphics.h"

/* Debugger-editable state. No wall-clock calibration or persistent RTC yet. */
volatile uint32_t g_clock_minute_of_day=0U;
volatile uint32_t g_clock_period_ms=60000U;
volatile uint32_t g_clock_next_tick=0U;
volatile uint32_t g_clock_running=1U;
extern volatile uint32_t g_force_clock_redraw;

static int clock_draw(uint8_t full_refresh)
{
    uint32_t value=g_clock_minute_of_day%1440U;
    gfx_clock((uint8_t)(value/60U),(uint8_t)(value%60U));
    if(!epd_clock_refresh(full_refresh)) { return 0; }
    if(full_refresh) {
        /* Equalize the digits initially written with the OTP waveform.
         * This one-time redraw also follows the hourly full refresh. */
        g_force_clock_redraw=1U;
        if(!epd_clock_refresh(0)) { g_force_clock_redraw=0U; return 0; }
        g_force_clock_redraw=0U;
    }
    return 1;
}

static int clock_advance(void)
{
    g_clock_minute_of_day=(g_clock_minute_of_day+1U)%1440U;
    return clock_draw((uint8_t)((g_clock_minute_of_day%60U)==0U));
}

/* 9=single minute, 10=full recovery at current time, 11=six fast minutes,
 * 12=apply g_clock_minute_of_day and rearm next deadline (no forced full).
 * Automatic deadlines use elapsed milliseconds, not refresh completion. */
void clock_run(void)
{
    uint32_t request,count,next_fast;
    if(!clock_draw(1)) { return; }
    g_clock_next_tick=g_status.ticks_ms+g_clock_period_ms;
    while(1) {
        request=g_status.command;
        if(request==10U) {
            g_status.command=0;
            if(!clock_draw(1)) { return; }
        } else if(request==9U) {
            g_status.command=0;
            if(!clock_advance()) { return; }
            g_clock_next_tick=g_status.ticks_ms+g_clock_period_ms;
        } else if(request==12U) {
            g_status.command=0;
            g_clock_minute_of_day%=1440U;
            if(!clock_draw(0)) { return; }
            g_clock_next_tick=g_status.ticks_ms+g_clock_period_ms;
        } else if(request==11U) {
            g_status.command=0;
            next_fast=g_status.ticks_ms+1000U;
            for(count=0;count<6U;count++) {
                while((int32_t)(g_status.ticks_ms-next_fast)<0 && !g_status.command) { __WFI(); }
                if(g_status.command) { break; }
                if(!clock_advance()) { return; }
                next_fast=g_status.ticks_ms+1000U;
            }
            g_clock_next_tick=g_status.ticks_ms+g_clock_period_ms;
        } else if(g_clock_running && (int32_t)(g_status.ticks_ms-g_clock_next_tick)>=0) {
            if(g_clock_period_ms<20000U) { g_clock_period_ms=60000U; }
            g_clock_next_tick+=g_clock_period_ms;
            if(!clock_advance()) { return; }
        }
        __WFI();
    }
}
