"""J-Link adapter for the existing verified NVMCTRL row programmer."""
import os
import pylink
from pyocd.core.target import Target

class JLinkTarget:
    def __init__(self):
        self.j = pylink.JLink(lib=pylink.library.Library(dllpath=os.environ.get('JLINK_DLL',r'C:\Program Files (x86)\SEGGER\JLink\JLink_x64.dll')))
        serial=os.environ.get('JLINK_SERIAL')
        self.j.open(serial_no=int(serial)) if serial else self.j.open()
        self.j.set_tif(pylink.enums.JLinkInterfaces.SWD)
        self.j.connect('Cortex-M0',speed=1000)
    def read8(self,a): return self.j.memory_read8(a,1)[0]
    def read16(self,a): return self.j.memory_read16(a,1)[0]
    def read32(self,a): return self.j.memory_read32(a,1)[0]
    def write8(self,a,v): self.j.memory_write8(a,[v])
    def write16(self,a,v): self.j.memory_write16(a,[v])
    def write32(self,a,v): self.j.memory_write32(a,[v])
    def read_memory_block8(self,a,n): return self.j.memory_read8(a,n)
    def read_memory_block32(self,a,n): return self.j.memory_read32(a,n)
    def write_memory_block32(self,a,v): self.j.memory_write32(a,v)
    def read_core_register(self,n): return self.j.register_read({'pc':15,'sp':13,'lr':14}.get(n,n.upper()))
    def halt(self): self.j.halt()
    def resume(self): self.j.restart()
    def flush(self): pass
    def get_state(self): return Target.State.HALTED if self.j.halted() else Target.State.RUNNING

class JLinkSession:
    def __enter__(self):
        self.target=JLinkTarget()
        return self
    def __exit__(self,*args): self.target.j.close()
