from pathlib import Path
from zipfile import ZipFile
import hashlib, json, re, xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[2]
out = root / 'outputs'
work = root / 'work' / 'diagnostics'
with ZipFile(r'D:\@Edgedownload\213资料\Microchip.SAMR21_DFP.2.1.155.atpack') as z:
    atdf = ET.fromstring(z.read('atdf/ATSAMR21G18A.atdf'))
    (work / 'ATSAMR21G18A.atdf').write_bytes(z.read('atdf/ATSAMR21G18A.atdf'))
    (work / 'samr21_pins.h').write_bytes(z.read('include/pio/samr21g18a.h'))
modules = {}
for m in atdf.findall('./modules/module'):
    groups = {}
    for g in m.findall('register-group'):
        groups[g.get('name')] = [dict(r.attrib) for r in g.findall('register')]
    modules[m.get('name')] = groups
(work / 'register_definitions.json').write_text(json.dumps(modules, indent=2), encoding='utf-8')
device = atdf.find('./devices/device')
summary = {'device': dict(device.attrib), 'address_spaces': [], 'peripherals': [], 'pinouts': []}
for a in device.findall('./address-spaces/address-space'):
    summary['address_spaces'].append({'attributes': dict(a.attrib), 'segments': [dict(x.attrib) for x in a.findall('memory-segment')]})
for m in device.findall('./peripherals/module'):
    for inst in m.findall('instance'):
        summary['peripherals'].append({'module': m.get('name'), 'attributes': dict(inst.attrib), 'register_groups': [dict(x.attrib) for x in inst.findall('register-group')], 'signals': [dict(x.attrib) for x in inst.findall('./signals/signal')]})
for p in atdf.findall('./pinouts/pinout'):
    summary['pinouts'].append({'attributes': dict(p.attrib), 'pins': [dict(x.attrib) for x in p.findall('pin')]})
(work / 'device_definition.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
manifest = []
for p in sorted(out.glob('original_*.bin')):
    data = p.read_bytes()
    manifest.append({'file': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
flash = (out / 'original_flash_256KiB_read1.bin').read_bytes()
second = (out / 'original_flash_256KiB_read2.bin').read_bytes()
assert len(flash) == len(second) == 0x40000
assert flash == second, 'Two Flash backups differ!'
strings = [(m.start(), m.group().decode('ascii')) for m in re.finditer(rb'[\x20-\x7e]{5,}', flash)]
(work / 'firmware_strings.txt').write_text('\n'.join(f'{a:08x} {s}' for a,s in strings), encoding='utf-8')
result = {'flash_backups_identical': True, 'backups': manifest,
          'last_non_ff_address': hex(max(i for i,b in enumerate(flash) if b != 255)),
          'initial_sp': hex(int.from_bytes(flash[:4], 'little')), 'reset_vector': hex(int.from_bytes(flash[4:8], 'little')),
          'printable_strings': len(strings)}
(out / 'backup_manifest.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
print('MODULES', list(modules))
for name in ['PORT','SERCOM','PM','SYSCTRL','GCLK','WDT','NVMCTRL','RFCTRL','RTC','EIC']:
    print(name, json.dumps(modules.get(name), ensure_ascii=False))
print('STRINGS', strings[:90])
