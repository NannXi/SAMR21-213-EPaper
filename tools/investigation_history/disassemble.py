from pathlib import Path
import json,struct
from capstone import *
from capstone.arm import *

root=Path(__file__).resolve().parents[2]
data=(root/'outputs/original_flash_256KiB_read1.bin').read_bytes()
dev=json.loads((root/'work/diagnostics/device_definition.json').read_text())
bases={int(g['offset'],0):p['attributes']['name'] for p in dev['peripherals'] for g in p['register_groups']}
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_LITTLE_ENDIAN|CS_MODE_MCLASS)
md.detail=True
md.skipdata=True
rows=[]; literals=[]; calls=[]
for ins in md.disasm(data[:0x13E40],0):
    extra=''
    if ins.id and ins.mnemonic.startswith('ldr') and len(ins.operands)>=2 and ins.operands[1].type==ARM_OP_MEM and ins.operands[1].mem.base==ARM_REG_PC:
        loc=((ins.address+4)&~3)+ins.operands[1].mem.disp
        if loc+4<=len(data):
            val=struct.unpack_from('<I',data,loc)[0]
            extra=f' ; literal [{loc:08x}]=0x{val:08x}'
            if val in bases: extra+=f' {bases[val]}'
            elif 0x40000000<=val<0x43000000:
                base=val&~0x3ff
                if base in bases: extra+=f' {bases[base]}+0x{val-base:x}'
            literals.append({'pc':ins.address,'pool':loc,'value':val,'annotation':extra})
    if ins.id and ins.mnemonic in ('bl','blx') and ins.operands[0].type==ARM_OP_IMM:
        calls.append({'pc':ins.address,'target':ins.operands[0].imm})
    rows.append(f'{ins.address:08x}: {ins.bytes.hex():10s} {ins.mnemonic:8s} {ins.op_str}{extra}')
(root/'work/diagnostics/firmware_thumb.asm').write_text('\n'.join(rows),encoding='utf-8')
(root/'work/diagnostics/literal_references.json').write_text(json.dumps(literals,indent=2),encoding='utf-8')
(root/'work/diagnostics/call_references.json').write_text(json.dumps(calls,indent=2),encoding='utf-8')
print('Peripheral constant references:')
for ref in literals:
    if 0x40000000<=ref['value']<0x43000000 or ref['value'] in (0x60000000,0x60000010,0x60000018):
        print(hex(ref['pc']),ref['annotation'])
print('Candidate vector tables:')
for off in range(0,len(data)-64,0x100):
    sp,entry=struct.unpack_from('<II',data,off)
    if 0x20000000<=sp<=0x20008000 and entry&1 and (entry&~1)<0x40000:
        print(hex(off),hex(sp),hex(entry))
