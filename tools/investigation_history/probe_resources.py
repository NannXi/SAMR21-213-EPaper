"""Inspect original SAMR21 firmware. No reset, erase, flash, or peripheral writes.
Only debugger attach and a short halt/resume are used for the core/RAM snapshot.
Peripheral DATA/FIFO and write-only registers are deliberately excluded.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, time, traceback, xml.etree.ElementTree as ET
from pyocd.core.helpers import ConnectHelper
from pyocd.core.target import Target

root = Path(__file__).resolve().parents[2]
out = root / 'outputs'
defs = json.loads((root/'work/diagnostics/register_definitions.json').read_text())
dev = json.loads((root/'work/diagnostics/device_definition.json').read_text())
report = {'utc': datetime.now(timezone.utc).isoformat(), 'method': 'attach, read-only peripheral inspection, brief core halt/RAM read; no reset/program/erase', 'registers': {}, 'errors': []}
session = ConnectHelper.session_with_chosen_probe(blocking=False, unique_id='37FF71064E57343693001043', options={
    'target_override':'cortex_m', 'frequency':100000, 'connect_mode':'attach', 'auto_unlock':False,
    'resume_on_disconnect':False, 'pack.debug_sequences.enable':False, 'no_config':True,
    'cache.enable_memory':False, 'cache.enable_register':False,
})
if session is None:
    raise SystemExit('No ST-Link found')

with session:
    target = session.target
    def read(name, address, size):
        try:
            value = target.read_memory(address, size*8)
            report['registers'][name] = {'address':f'0x{address:08X}', 'bytes':size, 'value':f'0x{value:0{size*2}X}'}
            return value
        except Exception as exc:
            report['errors'].append({'name':name, 'address':hex(address), 'error':str(exc)})
            return None
    report['probe'] = {'serial':session.probe.unique_id, 'firmware': session.probe._link.version_str,
                       'reported_target_voltage':session.probe._link.target_voltage}
    report['initial_state'] = str(target.get_state())
    read('CPUID',0xE000ED00,4)
    read('VTOR',0xE000ED08,4)
    read('SCR',0xE000ED10,4)
    read('DSU.DID',0x41002118,4)
    read('DSU.STATUSA',0x41002101,1)
    read('DSU.STATUSB',0x41002102,1)
    for name in ['PM','WDT','SYSCTRL','GCLK','NVMCTRL','EIC','RFCTRL']:
        inst = next(p for p in dev['peripherals'] if p['attributes']['name']==name)
        base = int(inst['register_groups'][0]['offset'],0)
        group = defs[name][name]
        for reg in group:
            if reg['rw']=='W' or reg['name'] in ['DFLLVAL','DFLLSYNC']:
                continue
            count=int(reg.get('count','1'))
            for index in range(count):
                suffix=f'[{index}]' if count>1 else ''
                read(f'{name}.{reg["name"]}{suffix}',base+int(reg['offset'],0)+index*int(reg['size']),int(reg['size']))
    for group_index, letter in enumerate('ABC'):
        base=0x41004400+group_index*0x80
        for name,offset in [('DIR',0),('OUT',0x10),('IN',0x20),('CTRL',0x24)]:
            read(f'PORT{letter}.{name}',base+offset,4)
        for name,offset,size in [('PMUX',0x30,16),('PINCFG',0x40,32)]:
            try:
                data=bytes(target.read_memory_block8(base+offset,size))
                report['registers'][f'PORT{letter}.{name}']={'address':hex(base+offset),'bytes':size,'hex':data.hex()}
            except Exception as exc:
                report['errors'].append({'name':f'PORT{letter}.{name}','error':str(exc)})
    # Read configuration/status only. Never read SERCOM DATA, USB endpoints, ADC RESULT, or radio SPI.
    sercom_regs=[('CTRLA',0,4),('CTRLB',4,4),('BAUD',0xC,2),('INTENSET',0x16,1),('INTFLAG',0x18,1),('STATUS',0x1A,2),('SYNCBUSY',0x1C,4),('DBGCTRL',0x30,1)]
    for index in range(6):
        for name,offset,size in sercom_regs:
            read(f'SERCOM{index}.{name}',0x42000800+index*0x400+offset,size)
    for name,address,size in [('NVIC.ISER',0xE000E100,4),('NVIC.ISPR',0xE000E200,4),('USB.CTRLA',0x41005000,1),('ADC.CTRLA',0x42004000,1),('ADC.INPUTCTRL',0x42004010,4)]:
        read(name,address,size)
    for index in range(3):
        read(f'TCC{index}.CTRLA',0x42002000+index*0x400,4)
    for index in range(3,6):
        read(f'TC{index}.CTRLA',0x42002C00+(index-3)*0x400,2)
    # Increase SWD only after comparing a Flash sample against the verified backup.
    sample=(out/'original_flash_256KiB_read1.bin').read_bytes()[:4096]
    session.probe.set_clock(1000000)
    readback=bytes(target.read_memory_block8(0,4096))
    if readback!=sample:
        raise RuntimeError('1 MHz Flash sample differs from verified backup; stop')
    report['verified_swd_frequency_hz']=1000000
    initial=target.get_state()
    halt_started=time.monotonic()
    resume_needed=initial in (Target.State.RUNNING,Target.State.SLEEPING)
    try:
        if resume_needed:
            target.halt()
        if target.get_state()==Target.State.HALTED:
            regs=['r'+str(i) for i in range(13)]+['sp','lr','pc','xpsr','msp','psp','primask','control']
            values=target.read_core_registers_raw(regs)
            report['cpu_registers']={r:f'0x{v:08X}' for r,v in zip(regs,values)}
            ram=bytes(target.read_memory_block8(0x20000000,0x8000))
            (out/'original_sram_snapshot_32KiB.bin').write_bytes(ram)
            report['ram_snapshot_bytes']=len(ram)
        else:
            report['errors'].append({'name':'halt','error':str(target.get_state())})
    finally:
        if resume_needed and target.get_state()==Target.State.HALTED:
            target.resume()
        report['halt_duration_seconds']=round(time.monotonic()-halt_started,3)
        report['final_state']=str(target.get_state())
    # Full auxiliary rows retained as backup evidence, without writing them.
    for name,address,size in [('original_user_row_256B.bin',0x00804000,0x100),('original_aux1_256B.bin',0x00806000,0x100),('original_aux3_256B.bin',0x0080A000,0x100),('original_lockbits_4B.bin',0x00802000,4),('original_cal_8B.bin',0x00800000,8)]:
        try:
            (out/name).write_bytes(bytes(target.read_memory_block8(address,size)))
        except Exception as exc:
            report['errors'].append({'name':name,'error':str(exc)})

(out/'hardware_snapshot.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='registers'},indent=2))
for k,v in report['registers'].items():
    print(k,v.get('value',v.get('hex')))
