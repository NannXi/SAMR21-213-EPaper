# SAMR21 2.13 寸大字局刷时钟（实验版）

![逻辑帧预览，非实物照片](clock_1234_preview.png)

2026-10-27，LG Innotek TAG2.13B / ATSAMR21G18A / WF0213T50CZ16E41e，横向 212×104。用户选择字体 C：Oswald，保留 88 像素高数字单元，保持原始字形比例。

## 时钟行为

- 二十四小时 HH:MM，只显示时间；数字单元 44×88，左右约 5、上下 8 像素边距。
- 每 60,000 ms 走一分钟；按绝对毫秒截止时间推进，不把每次刷新耗时加进分钟长度。使用未校准内部 8 MHz，断电不保存时间。
- 平时只擦写变化的数字格；冒号、其他数字保持。虽传完整旧/新帧，零 WW/BB 波形使非变化区域不参与更新。
- 先擦白 60 帧、再写黑 100 帧，PLL 0x3A，实测两段约 2.36 秒。
- 整点使用原厂三色 OTP 全刷一次（约 14.97 秒），随后统一重画数字，尝试改善全刷字偏灰而局刷字偏黑的问题。启动也执行此序列。
- 变化数字格内逻辑为白、实物可能残红的像素也擦白。这是白向脉冲实验，未完成红色专用波形标定。

## 显示质量

用户已确认单数字局刷有效，比整串擦写好很多。更新后背景有暂时淡粉色，静置后减淡；擦除 120 降到 60 帧后反馈“还是有一点点，但是好很多”。不能将此称为无残影，也不能据此断言屏幕老化。当前为用户选择的 C 款 Oswald 字体；C 字体已烧录，工具验证末位变化范围、自动走分和午夜整点全刷完成；实物颜色与长期残影仍需观察。

驱动行为属于 UC8151 / IL0373 兼容家族；精确 die 修订号未直接确认。RESE 0.47 ohm 是线索，OTP 4096 字节、分辨率与指令行为是更强证据。

## 编译

与相邻 SAMR21_EPD_Keil 共用 Device/CMSIS、已验证的原厂恢复镜像和 NVMCTRL 行编程器，不能单独搬走本目录。

    .\build.ps1 -KeilRoot D:\12-keil5

使用 Keil ARMCC 5.06，输出 Objects/epd_clock.axf、.bin、.hex。也可打开 SAMR21_213_Clock.uvprojx；烧录仍走下面的工具。

## J-Link OB 烧录与设时

    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r Tools\requirements.txt
    $env:JLINK_DLL='C:\Program Files (x86)\SEGGER\JLink\JLink_x64.dll'
    .\flash.ps1 flash
    .\flash.ps1 status
    .\flash.ps1 set-time -Time '12:34'
    .\flash.ps1 step

需先安装 SEGGER J-Link。默认 DLL 路径如上，可用 JLINK_DLL 修改，多个探针时设 JLINK_SERIAL。工具不提交本机探针序列号。

set-time 只在当前上电周期有效，下一次跳分从显示完成后计 60 秒，未授时或校准。正常自动时钟不在每次显示结束后重算一分钟。

step 手动加一分钟；full 原厂全刷当前时间；test6 连续六次加速，随后恢复分钟周期。固件和 AXF 必须配套。烧录前双份读取当前 Flash，写后核对全 256 KiB 及辅助区；无屏 OTP 写入、无熔丝修改、无芯片擦除。原厂恢复继续使用相邻工程既有 ST-Link 恢复工具。

## 字库与波形参考

字体源和许可在 Assets 内；Tools/generate_clock_font.py 可重建字库与预览，Pillow 依赖见 Tools/font-requirements.txt。MCU 不运行字体引擎。

- UltraChip UC8151c datasheet：指令和 LUT 数据格式参考，不能据此确认本屏 die 修订。
- [GxEPD2_213_flex](https://github.com/ZinggJM/GxEPD2/blob/master/src/epd/GxEPD2_213_flex.cpp)：差分波形格式参考，不宣称采用该黑白柔性屏的原厂波形。
- [Oswald](https://github.com/google/fonts/tree/main/ofl/oswald)：SIL OFL 1.1，文件与许可在 Assets/Oswald。

更多过程见 [实验记录](../../docs/PARTIAL_CLOCK_20261027.md)。validation 记录工具回读状态，不能把 BUSY 结束等同于光学效果合格。
