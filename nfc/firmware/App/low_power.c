#include "app.h"
#include "low_power.h"

void low_power_init(void)
{
    /* Keep PORT, PM, SYSCTRL, GCLK and SERCOM1 only. RF is external to the MCU;
       without a verified GPO pin, mailbox polling remains the safe wake path. */
    PM_REGS->PM_APBAMASK=PM_APBAMASK_PM_Msk|PM_APBAMASK_SYSCTRL_Msk|PM_APBAMASK_GCLK_Msk;
    PM_REGS->PM_APBBMASK=PM_APBBMASK_PORT_Msk;
    PM_REGS->PM_APBCMASK=PM_APBCMASK_SERCOM1_Msk;
    PM_REGS->PM_SLEEP=PM_SLEEP_IDLE_CPU;
    SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;
}

void low_power_idle(void) { __WFI(); }
