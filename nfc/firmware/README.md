# Keil5 固件

## 当前合并固件 v0.2.0

同一个固件接收图片和授时命令；App/device_clock.c驱动24小时分钟时钟，支持每分钟全刷或局刷＋1–24小时全刷。Drivers/epd.c保留原厂全刷，局刷沿用已确认的60帧擦除/100帧写黑与C款Oswald字体。配置、时间与图片不掉电保存，未校准。

Objects/epd_white.bin/.hex/.axf名称保留，Release另命名samr21-unified-v0.2.0。当前下载默认J-Link OB，依赖pylink-square与SEGGER DLL，可设JLINK_SERIAL/JLINK_DLL；EPD_DEBUGGER=stlink切回旧ST-Link路径，使用EPD_PROBE_SERIAL。SWD引脚不变。recover仍使用旧ST-Link工具，不能直接视为J-Link恢复路径。

下载先备份、双读和设备核对，最终全Flash回读、未写区与辅助区比对；不整片擦除、不改熔丝/锁。详见[合并验证](../docs/UNIFIED_20261027.md)。

## 旧版接线与构建基础（默认探针以本页上方为准）

MCU：ATSAMR21G18A，8 MHz，Cortex-M0+。打开 `SAMR21_EPD.uvprojx`，选择 ARM Compiler 5。源代码是 C/ASM；Python 仅用于电脑端 SWD 下载、备份与验证。

```powershell
.\build.ps1 -KeilRoot 'D:\12-keil5'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Tools/requirements.txt
.\flash.ps1 -Action flash
```

输出 `Objects/epd_white.axf/.bin/.hex` 名称继承初始工程，目前为 NFC 版。Release 同时提供清楚命名的 `samr21-nfc-v0.1.2.bin/.hex`，内容一致。Keil 内置下载用的 SAMR21 FLM 尚未配置，当前外部 SWD 工具是已验证路径。

保持已验证的 ST-Link 3.3 V/GND/PA31 SWDIO/PA30 SWCLK 接法。默认探针序列号沿用实物，可通过环境变量 `EPD_PROBE_SERIAL` 设置。工具先备份、双读一致后编程，最后写复位向量，再做 256 KiB 全量回读与辅助区校验。不要使用整片擦除或自动解锁。

`flash.ps1 -Action status` 读显示状态；`-Action recover` 恢复随附原板镜像。原厂镜像和 NFC EEPROM 备份包含本板标识，仅针对这块板，勿盲目用于其他硬件。主机解释器优先使用工程内.venv，也可通过 `-PythonExe` 指定。NFC EEPROM备份位于 [docs/nfc_eeprom_before.bin](../docs/nfc_eeprom_before.bin)，原厂Flash恢复不会恢复独立NFC EEPROM。每次运行的原始证据保存在未进 Git 的 `Runs/`。

- `App/protocol.c`：包解析、完整性、双缓冲提交。
- `Drivers/nfc.c`：SERCOM1 I²C 及 SRAM/会话寄存器，I²C 写函数限制在 SRAM，不提供 EEPROM 写操作。
- `Drivers/epd.c`：沿用已实测屏幕初始化和双色平面发送。
- `App/graphics.c`：内置示例和横向坐标；上电刷新一次，之后等待手机提交。
- 调试结构 `g_nfc` 与 `g_status` 保留；地址用当前 AXF 符号表解析，不能硬编码旧地址。

当前不启用片内 2.4 GHz 无线，不改锁位/熔丝，不实现电池休眠和上传图像掉电保存。更详见根 README 和协议文档。
