"""Read-only test of Microchip's reset-and-halt sequence; no NVM commands."""
from pathlib import Path
import json,time
from pyocd.core.helpers import ConnectHelper
from pyocd.core.target import Target

out=Path(__file__).resolve().parents[2]/'outputs'/'flash_reset_catch.json'
report={'method':'Microchip reset_and_halt: DEMCR.VC_CORERESET, SYSRESETREQ, DHCSR.C_HALT, DSU.CRSTEXT W1C; no hardware breakpoint and no NVM commands','events':[]}
session=ConnectHelper.session_with_chosen_probe(blocking=False,unique_id='37FF71064E57343693001043',options={
 'target_override':'cortex_m','frequency':1000000,'connect_mode':'attach','auto_unlock':False,
 'resume_on_disconnect':False,'pack.debug_sequences.enable':False,'no_config':True,
 'cache.enable_memory':False,'cache.enable_register':False})
with session:
 t=session.target
 try:
  t.halt()
  old_demcr=t.read32(0xe000edfc)
  t.write32(0xe000edfc,old_demcr|0x01000001)
  t.write32(0xe000ed0c,0x05fa0004)
  t.flush()
  deadline=time.monotonic()+3
  while time.monotonic()<deadline:
   dhcsr=t.read32(0xe000edf0)
   statusa=t.read8(0x41002101)
   report['events'].append({'dhcsr':hex(dhcsr),'dsu_statusa':hex(statusa)})
   if dhcsr&0x02000000 or statusa&2:
    t.write32(0xe000edf0,0xa05f0003)
    if statusa&2: t.write8(0x41002101,2)
    t.flush()
   if t.get_state()==Target.State.HALTED and not t.read8(0x41002101)&2:
    break
   time.sleep(.01)
  report['state']=str(t.get_state())
  report['pc']=hex(t.read_core_register('pc'))
  report['boot_reset_vector']=hex(t.read32(4))
  report['success']=t.get_state()==Target.State.HALTED and (t.read_core_register('pc')&~1)==(t.read32(4)&~1)
 finally:
  t.write32(0xe000edfc,old_demcr)
  t.flush()
  if t.get_state()==Target.State.HALTED: t.resume()
  report['final_state']=str(t.get_state())
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if not report['success']: raise SystemExit(1)
