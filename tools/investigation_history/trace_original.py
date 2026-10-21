"""Observe one original firmware boot with hardware breakpoints only.
Writes only debugger controls, AIRCR SYSRESETREQ and DSU CRSTEXT; no injected code.
The firmware performs its normal startup, including any normal NDEF/config updates.
"""
from pathlib import Path
from datetime import datetime,timezone
import time,json,traceback
from pyocd.core.helpers import ConnectHelper
from pyocd.core.target import Target

root=Path(__file__).resolve().parents[2]; out=root/'outputs'
report={'utc':datetime.now(timezone.utc).isoformat(),'events':[],'errors':[],
 'method':'one original firmware system reset; hardware breakpoints only; no flash programming, no code injection'}
session=ConnectHelper.session_with_chosen_probe(blocking=False,unique_id='37FF71064E57343693001043',options={
 'target_override':'cortex_m','frequency':1000000,'connect_mode':'attach','auto_unlock':False,
 'resume_on_disconnect':False,'pack.debug_sequences.enable':False,'no_config':True,
 'cache.enable_memory':False,'cache.enable_register':False})
active={}; pending=None; commands=[]; group=None; data_count=0; read_count=0
report['epd_commands']=commands
def event(kind,**kwargs):
 row={'kind':kind,**kwargs}; report['events'].append(row)
 if kind!='epd_data': print(json.dumps(row),flush=True)
def add(t,addr,label):
 if not t.set_breakpoint(addr,Target.BreakpointType.HW): raise RuntimeError('No hardware breakpoint: '+label)
 t.selected_core.bp_manager.flush()
 if t.get_breakpoint_type(addr)!=Target.BreakpointType.HW: raise RuntimeError('Hardware breakpoint was not installed: '+label)
 active[addr]=label
def remove(t,addr):
 if addr in active:
  t.remove_breakpoint(addr); t.selected_core.bp_manager.flush(); del active[addr]
try:
 with session:
  t=session.target
  try:
   report['before_state']=str(t.get_state())
   in_reset=bool(t.read8(0x41002101)&2)
   if not in_reset:
    t.halt()
    limit=time.monotonic()+1
    while t.get_state()!=Target.State.HALTED and time.monotonic()<limit: time.sleep(.005)
    if t.get_state()!=Target.State.HALTED: raise RuntimeError('Unable to halt before trace')
   for addr,label in [(0xd6c,'display_create'),(0x14bc,'epd_command'),(0x44b8,'nfc_read_entry'),(0x44c2,'nfc_read_exit')]: add(t,addr,label)
   report['breakpoint_types']={hex(a):str(t.get_breakpoint_type(a)) for a in active}
   if any(t.get_breakpoint_type(a)!=Target.BreakpointType.HW for a in active): raise RuntimeError('Non-hardware breakpoint refused')
   event('breakpoints_installed',fp_ctrl=hex(t.read32(0xE0002000)),comparators=[hex(t.read32(0xE0002008+i*4)) for i in range(4)])
   if not in_reset:
    t.write32(0xE000ED0C,0x05FA0004); t.flush()
    time.sleep(.05)
   else:
    event('already_in_reset_extension',action='release existing reset; do not request another')
   if t.read8(0x41002101)&2: t.write8(0x41002101,2); t.flush()
   if t.get_state()==Target.State.HALTED:
    pc=t.read_core_register('pc')&~1
    if pc not in active: t.resume()
   event('after_system_reset',state=str(t.get_state()),dsu_statusa=hex(t.read8(0x41002101)),dhcsr=hex(t.read32(0xE000EDF0)),fp_ctrl=hex(t.read32(0xE0002000)))
   deadline=time.monotonic()+30
   while time.monotonic()<deadline and len(report['events'])<600:
    if t.get_state()!=Target.State.HALTED:
     time.sleep(.005); continue
    regs=t.read_core_registers_raw(['r0','r1','r2','r3','sp','lr','pc'])
    r0,r1,r2,r3,sp,lr,pc=regs; pc&=~1
    kind=active.get(pc)
    if kind is None:
     event('unexpected_halt',pc=hex(pc),lr=hex(lr)); break
    if kind=='display_create':
     event(kind,panel_model=r0,driver_family=r1,caller=hex(lr))
     remove(t,pc)
     add(t,0xb106,'nfc_setup_finished')
    elif kind=='nfc_read_entry':
     pending={'block':r0&255,'buffer':r1,'caller':hex(lr)}
    elif kind=='nfc_read_exit':
     if pending:
      payload=bytes(t.read_memory_block8(pending['buffer'],16))
      event('nfc_read',block=pending['block'],buffer=hex(pending['buffer']),hex=payload.hex(),i2c_return=r0,caller=pending['caller'])
      report['nfc_i2c_live']={name:hex(t.read32(addr)) for name,addr in [('CTRLA',0x42000c00),('BAUD',0x42000c0c)]}
      pending=None; read_count+=1
      if read_count>=12: remove(t,0x44b8); remove(t,0x44c2)
    elif kind=='nfc_setup_finished':
     event(kind)
     remove(t,pc); remove(t,0x44b8); remove(t,0x44c2)
     add(t,0x1508,'epd_data')
     add(t,0x97d4,'spi_flash_read')
    elif kind=='epd_command':
     group={'command':r0&255,'data':[],'caller':hex(lr)}; commands.append(group)
     event(kind,command=hex(r0&255),caller=hex(lr))
     if 'epd_spi_live' not in report:
      report['epd_spi_live']={name:hex(t.read32(addr)) for name,addr in [('CTRLA',0x42001400),('CTRLB',0x42001404),('BAUD',0x4200140c),('PORTA.DIR',0x41004400),('PORTA.OUT',0x41004410),('PORTB.DIR',0x41004480),('PORTB.OUT',0x41004490)]}
     if r0&255==0x12:
      event('trace_complete_before_refresh',reason='avoid polling through deep sleep; let original complete refresh after cleanup')
      break
     if r0&255 in (0x10,0x13,0x24,0x26):
      # Image payload can be thousands of bytes. Leave it running at full speed.
      remove(t,0x1508)
    elif kind=='epd_data':
     if group: group['data'].append(r0&255)
     data_count+=1
     if data_count>=160: remove(t,pc)
    elif kind=='spi_flash_read':
     event(kind,address=hex(r0),buffer=hex(r1),length=r2,caller=hex(lr))
     remove(t,pc)
    if pc in active:
     label=active[pc]
     remove(t,pc)
     t.step()
     add(t,pc,label)
    t.resume()
   report['epd_commands']=commands
   t.halt()
   report['post_trace_pc']=hex(t.read_core_register('pc'))
   (out/'original_sram_after_trace_32KiB.bin').write_bytes(bytes(t.read_memory_block8(0x20000000,0x8000)))
   flash=bytes(t.read_memory_block8(0,0x40000))
   (out/'original_flash_postdebug_256KiB.bin').write_bytes(flash)
   original=(out/'original_flash_256KiB_read1.bin').read_bytes()
   changed=[i for i,(a,b) in enumerate(zip(original,flash)) if a!=b]
   report['flash_comparison']={'changed_byte_count':len(changed),'first_changed':hex(changed[0]) if changed else None,'last_changed':hex(changed[-1]) if changed else None,'code_and_initial_data_match':original[:0x1453c]==flash[:0x1453c]}
   for name,address,size in [('postdebug_user_row_256B.bin',0x00804000,256),('postdebug_aux1_256B.bin',0x00806000,256),('postdebug_aux3_256B.bin',0x0080A000,256)]:
    (out/name).write_bytes(bytes(t.read_memory_block8(address,size)))
  except Exception as exc:
   report['errors'].append(str(exc)); traceback.print_exc()
  finally:
   for a in list(active):
    try: remove(t,a)
    except Exception as exc: report['errors'].append('breakpoint cleanup '+str(exc))
   if t.get_state()==Target.State.HALTED: t.resume()
   report['final_state']=str(t.get_state())
finally:
 (out/'original_boot_trace.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='events'},indent=2),flush=True)
