/* Board mapping and initialization reconstructed from the backed-up firmware.
 * Software SPI mode 3 avoids dependence on the factory's 48 MHz clock setup.
 * Full refresh retains the OTP waveform and original voltage setup.
 * Clock partial refresh uses the tested 60-frame erase / 100-frame draw LUT.
 */
#include "app.h"
#include "graphics.h"
#define PA_CS    (1UL<<23)
#define PA_SDIO  (1UL<<24)
#define PA_CLK   (1UL<<25)
#define PA_BUSY  (1UL<<27)
#define PA_POWER (1UL<<28)
#define PB_DC    (1UL<<22)
#define PB_RESET (1UL<<23)
#define A (PORT_REGS->GROUP[0])
#define B (PORT_REGS->GROUP[1])

static void edge_delay(void) { __NOP(); __NOP(); __NOP(); __NOP(); }
static void spi_byte(uint8_t value)
{
    uint32_t bit;
    for (bit=0; bit<8; bit++) {
        A.PORT_OUTCLR = PA_CLK;
        if (value & 0x80U) { A.PORT_OUTSET = PA_SDIO; }
        else { A.PORT_OUTCLR = PA_SDIO; }
        edge_delay();
        A.PORT_OUTSET = PA_CLK;
        edge_delay();
        value <<= 1;
    }
}

static void command(uint8_t value)
{
    g_status.last_epd_command=value;
    B.PORT_OUTCLR=PB_DC;
    A.PORT_OUTCLR=PA_CS;
    spi_byte(value);
    A.PORT_OUTSET=PA_CS;
}

static void data(uint8_t value)
{
    B.PORT_OUTSET=PB_DC;
    A.PORT_OUTCLR=PA_CS;
    spi_byte(value);
    A.PORT_OUTSET=PA_CS;
    g_status.bytes_sent++;
}

static uint32_t busy_high(void)
{
    uint32_t high = (A.PORT_IN & PA_BUSY) != 0U;
    g_status.busy = !high;
    return high;
}

void epd_emergency_off(void)
{
    A.PORT_OUTCLR=PA_POWER|PA_CLK|PA_SDIO|PA_CS;
    B.PORT_OUTCLR=PB_RESET|PB_DC;
}

static int wait_ready(uint32_t timeout_ms, uint32_t error)
{
    uint32_t start=g_status.ticks_ms;
    while (!busy_high()) {
        g_status.busy_wait_ms=g_status.ticks_ms-start;
        if (g_status.busy_wait_ms >= timeout_ms) {
            g_status.error=error;
            g_status.stage=0xe0;
            epd_emergency_off();
            return 0;
        }
        delay_ms(1);
    }
    g_status.busy_wait_ms=g_status.ticks_ms-start;
    return 1;
}

static uint8_t temperature_read(void)
{
    uint32_t bit;
    uint8_t result=0;
    B.PORT_OUTCLR=PB_DC;
    A.PORT_OUTCLR=PA_CS;
    spi_byte(0x40);
    A.PORT_DIRCLR=PA_SDIO;
    A.PORT_PINCFG[24]=PORT_PINCFG_INEN_Msk;
    B.PORT_OUTSET=PB_DC;
    for (bit=0;bit<8;bit++) {
        A.PORT_OUTCLR=PA_CLK;
        edge_delay();
        A.PORT_OUTSET=PA_CLK;
        edge_delay();
        result=(uint8_t)((result<<1)|((A.PORT_IN&PA_SDIO)!=0U));
    }
    A.PORT_OUTSET=PA_CS;
    A.PORT_PINCFG[24]=0;
    A.PORT_DIRSET=PA_SDIO;
    return result;
}

void epd_gpio_init(void)
{
    uint32_t pin;
    PM_REGS->PM_APBBMASK |= PM_APBBMASK_PORT_Msk;
    for(pin=23;pin<=28;pin++) {
        if(pin!=26U) { A.PORT_PINCFG[pin]=0; }
    }
    B.PORT_PINCFG[22]=0;
    B.PORT_PINCFG[23]=0;
    A.PORT_OUTCLR=PA_POWER;
    A.PORT_OUTSET=PA_CS|PA_CLK|PA_SDIO;
    B.PORT_OUTSET=PB_RESET|PB_DC;
    A.PORT_DIRSET=PA_CS|PA_CLK|PA_SDIO|PA_POWER;
    B.PORT_DIRSET=PB_RESET|PB_DC;
    A.PORT_DIRCLR=PA_BUSY;
    A.PORT_PINCFG[27]=PORT_PINCFG_INEN_Msk;
}

static uint8_t plane_byte(uint32_t index, uint32_t red, uint32_t pattern)
{
    uint32_t x=(index%13U)*8U;
    uint32_t y=index/13U;
    if (pattern >= 3U) { return g_framebuffer[red][index]; }
    /* Factory 2bpp red code 2 maps to 0 in BOTH observed plane LUTs. */
    if (pattern == 2U) { return 0x00; }
    if (!pattern) { return 0xff; }
    /* Three horizontal areas in controller coordinates, no graphics library. */
    if (y>=24U && y<80U && x>=16U && x<88U && !red) { return 0x00; }
    if (y>=128U && y<184U && x>=16U && x<88U) { return 0x00; }
    return 0xff;
}

int epd_display(uint8_t border, uint32_t pattern)
{
    uint32_t i,start;
    if (pattern == 3U) { gfx_demo(); }
    g_status.stage=2;
    g_status.border=border;
    g_status.bytes_sent=0;
    A.PORT_OUTSET=PA_CS|PA_CLK|PA_SDIO;
    B.PORT_OUTSET=PB_RESET|PB_DC;
    delay_ms(20);
    A.PORT_OUTSET=PA_POWER;
    B.PORT_OUTCLR=PB_RESET;
    delay_ms(20);
    B.PORT_OUTSET=PB_RESET;
    delay_ms(20);
    command(0x06); data(0x17); data(0x17); data(0x17);
    command(0x04);
    delay_ms(5);
    if (!wait_ready(5000,1)) { return 0; }
    g_status.temperature_raw=temperature_read();
    command(0x00); data(0x0f);
    command(0x61); data(0x68); data(0x00); data(0xd4);
    command(0x50); data(border);
    g_status.stage=3;
    command(0x10);
    for(i=0;i<EPD_PLANE_BYTES;i++) { data(plane_byte(i,0,pattern)); }
    command(0x13);
    for(i=0;i<EPD_PLANE_BYTES;i++) { data(plane_byte(i,1,pattern)); }
    g_status.stage=4;
    start=g_status.ticks_ms;
    command(0x12);
    delay_ms(20);
    if (!wait_ready(45000,2)) { return 0; }
    g_status.refresh_ms=g_status.ticks_ms-start;
    g_status.stage=5;
    command(0x50); data(0xf7);
    command(0x02);
    delay_ms(5);
    if (!wait_ready(5000,3)) { return 0; }
    epd_emergency_off();
    delay_ms(100);
    return 1;
}


/* Short black/white differential experiment, not the panel's factory BWR LUT.
 * Structure follows UC8151/IL0373 and GxEPD2_213_flex: 44-byte VCOM,
 * 42-byte WW/BW/WB/BB, first 6-byte group active, unused groups zero.
 * No pulses for unchanged pixels. Native BWR OTP is used for recovery.
 */
static uint8_t previous_frame[EPD_PLANE_BYTES];
static uint8_t previous_valid;
volatile uint32_t g_partial_frames=60U;
volatile uint32_t g_erase_frames=60U;
volatile uint32_t g_draw_frames=100U;
static uint8_t erase_frame[EPD_PLANE_BYTES];
static uint8_t erase_source[EPD_PLANE_BYTES];
/* Drive the white background inside changed glyphs as well: its logical
 * white pixels can still contain visible red/black pigment on an old panel.
 * This is an experimental white-going pulse, not a calibrated red LUT. */
volatile uint32_t g_clear_ghost_pixels=1U;
volatile uint32_t g_force_clock_redraw=0U;
volatile uint32_t g_partial_swap=0U;
static void partial_lut(uint8_t cmd, uint8_t pattern, uint32_t length)
{
    uint32_t i;
    command(cmd);
    for(i=0;i<length;i++) {
        data(i==0U ? pattern : (i==1U ? (uint8_t)g_partial_frames : ((i==2U || i==5U) ? 1U : 0U)));
    }
}
int epd_clock_refresh(uint8_t full_refresh)
{
    uint32_t i,start,phase,pass_start,x,y,glyph,changed;
    const uint8_t *old_data,*new_data;
    if(full_refresh || !previous_valid) {
        g_status.refresh_mode=0;
        if(!epd_display(0x77U,4U)) { previous_valid=0; return 0; }
        /* pattern 4 means the caller-rendered framebuffer, no demo drawing. */
        for(i=0;i<EPD_PLANE_BYTES;i++) { previous_frame[i]=g_framebuffer[0][i]; }
        previous_valid=1;
        g_status.full_count++;
        g_status.completed++;
        g_status.stage=6;
        return 1;
    }
    g_status.stage=2;
    g_status.refresh_mode=1;
    g_status.bytes_sent=0;
    g_status.busy_seen=0;
    A.PORT_OUTSET=PA_CS|PA_CLK|PA_SDIO;
    B.PORT_OUTSET=PB_RESET|PB_DC;
    delay_ms(20);
    A.PORT_OUTSET=PA_POWER;
    B.PORT_OUTCLR=PB_RESET; delay_ms(20);
    B.PORT_OUTSET=PB_RESET; delay_ms(20);
    /* Start with the original OTP-based power-up to retain panel voltages. */
    command(0x06); data(0x17); data(0x17); data(0x17);
    command(0x04); delay_ms(5);
    if(!wait_ready(5000,1)) { return 0; }
    command(0x00); data(0x3f); /* original scan bits + B/W + RAM LUT */
    command(0x61); data(0x68); data(0x00); data(0xd4);
    command(0x30); data(0x3a); /* documented 100 Hz frame clock */
    command(0x50); data(0x17); /* B/W floating border */

    /* Use the exact digit-cell geometry exported by the clock renderer.
     * Erase only a glyph whose framebuffer has changed, then redraw it.
     * Unchanged digits, the colon and the border receive no drive pulses. */
    for(i=0;i<EPD_PLANE_BYTES;i++) {
        erase_frame[i]=previous_frame[i];
        erase_source[i]=previous_frame[i];
    }
    for(glyph=0;glyph<CLOCK_CELL_COUNT;glyph++) {
        changed=g_force_clock_redraw;
        for(x=g_clock_cell_x[glyph];x<(uint32_t)(g_clock_cell_x[glyph]+g_clock_cell_width[glyph]);x++) {
            for(y=CLOCK_TOP;y<CLOCK_TOP+CLOCK_HEIGHT;y++) {
                i=(211U-x)*13U+y/8U;
                if((previous_frame[i]^g_framebuffer[0][i]) & (0x80U>>(y&7U))) { changed=1; }
            }
        }
        if(changed) {
            for(x=g_clock_cell_x[glyph];x<(uint32_t)(g_clock_cell_x[glyph]+g_clock_cell_width[glyph]);x++) {
                for(y=CLOCK_TOP;y<CLOCK_TOP+CLOCK_HEIGHT;y++) {
                    i=(211U-x)*13U+y/8U;
                    erase_frame[i]|=(uint8_t)(0x80U>>(y&7U));
                    if(g_clear_ghost_pixels) { erase_source[i]&=(uint8_t)~(0x80U>>(y&7U)); }
                }
            }
        }
    }
    start=g_status.ticks_ms;
    for(phase=0;phase<2;phase++) {
        g_partial_frames=phase==0U ? g_erase_frames : g_draw_frames;
        partial_lut(0x20,0x00,44);
        partial_lut(0x21,0x00,42);
        partial_lut(0x22,g_partial_swap ? 0x40 : 0x80,42);
        partial_lut(0x23,g_partial_swap ? 0x80 : 0x40,42);
        partial_lut(0x24,0x00,42);
        old_data=phase==0U ? erase_source : erase_frame;
        new_data=phase==0U ? erase_frame : g_framebuffer[0];
        g_status.stage=3;
        command(0x10);
        for(i=0;i<EPD_PLANE_BYTES;i++) { data(old_data[i]); }
        command(0x13);
        for(i=0;i<EPD_PLANE_BYTES;i++) { data(new_data[i]); }
        command(0x11);
        g_status.stage=4;
        pass_start=g_status.ticks_ms;
        command(0x12);
        while(busy_high() && (uint32_t)(g_status.ticks_ms-pass_start)<100U) { delay_ms(1); }
        if(busy_high()) {
            g_status.error=0x201; g_status.stage=0xe0; epd_emergency_off(); return 0;
        }
        g_status.busy_seen=1;
        if(!wait_ready(5000,2)) { previous_valid=0; return 0; }
        delay_ms(40);
    }
    g_status.refresh_ms=g_status.ticks_ms-start;
    g_status.stage=5;
    command(0x02); delay_ms(5);
    if(!wait_ready(5000,3)) { return 0; }
    epd_emergency_off();
    for(i=0;i<EPD_PLANE_BYTES;i++) { previous_frame[i]=g_framebuffer[0][i]; }
    g_status.partial_count++;
    g_status.completed++;
    g_status.stage=6;
    return 1;
}
