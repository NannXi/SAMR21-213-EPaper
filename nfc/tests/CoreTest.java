import io.github.nannxi.epaper.*;
import java.util.*;

public final class CoreTest {
  static void check(boolean b, String s) {
    if (!b) throw new AssertionError(s);
  }

  public static void main(String[] args) {
    long stamp=1793054123456L;
    byte[] clock=ClockConfig.payload(stamp,480,1,6);
    check(clock.length==16 && clock[0]==1 && clock[1]==1 && clock[2]==6,"clock config schema");
    check(Wire.u32(clock,4)==stamp/1000 && Wire.u16(clock,8)==480 && Wire.u16(clock,10)==456,"clock time and subsecond");
    byte[] western=ClockConfig.payload(stamp,-330,0,24);
    check((short)Wire.u16(western,8)==-330 && western[1]==0,"negative timezone and full policy");
    int invalid=0;
    for(int[] c:new int[][]{{1,0,480},{1,25,480},{2,1,480},{1,1,841},{1,1,-841}}) {
      try{ClockConfig.payload(stamp,c[2],c[0],c[1]);}catch(IllegalArgumentException e){invalid++;}
    }
    check(invalid==5,"invalid settings rejected");
    byte[] clockFrame=Wire.packet(6,0,123,0,clock);
    check(clockFrame[5]==6 && clockFrame[14]==16 && Wire.crc(clockFrame,60)==Wire.u32(clockFrame,60),"clock wire CRC");
    int[] preview=ClockPreview.pixels(12,34), preview2=ClockPreview.pixels(12,35);int changed=0;
    for(int y=0;y<104;y++)for(int x=0;x<212;x++)if(preview[y*212+x]!=preview2[y*212+x]) {
      check(x>=163 && x<207 && y>=8 && y<96,"clock preview only last digit changes");changed++;
    }
    check(changed>0,"clock preview changes");
    System.out.println("PASS: clock config, signed timezone, bounds, packet CRC, exact glyph preview");
    int[] p = new int[212 * 104];
    Arrays.fill(p, 0xffffffff);
    byte[] a = ImageProcessor.pack(p);
    for (byte b : a) check(b == (byte) 255, "white");
    int[][] points = {{0, 0}, {211, 0}, {0, 103}, {211, 103}, {100, 50}};
    for (int[] point : points) {
      Arrays.fill(p, 0xffffffff);
      int x = point[0], y = point[1], index = (211 - x) * 13 + y / 8, mask = 0x80 >> (y % 8);
      p[y * 212 + x] = 0xff000000;
      a = ImageProcessor.pack(p);
      check((a[index] & mask) == 0 && (a[2756 + index] & mask) != 0, "black coordinate");
      p[y * 212 + x] = 0xffdc1c2d;
      a = ImageProcessor.pack(p);
      check((a[index] & mask) == 0 && (a[2756 + index] & mask) == 0, "red coordinate");
    }
    Arrays.fill(p, 0xff808080);
    int count = 0;
    for (int d = 0; d < 3; d++) {
      int[] colors = ImageProcessor.convert(p, 0, 0, d, true);
      for (int c : colors) {
        check(c == 0xffffffff || c == 0xff000000 || c == 0xffdc1c2d, "palette");
        if (c == 0xff000000) count++;
      }
    }
    for (int i = 0; i < p.length; i++) {
      int v = (i % 212) * 255 / 211;
      p[i] = 0xff000000 | (v << 16) | (v << 8) | v;
    }
    int[] plain = ImageProcessor.convert(p, 0, 0, 0, false);
    for (int mode = 1; mode <= 2; mode++) {
      check(
          Arrays.equals(plain, ImageProcessor.convert(p, 0, 0, mode, 0, false)),
          "zero strength equals no dithering");
      check(
          Arrays.equals(
              ImageProcessor.convert(p, 0, 0, mode, false),
              ImageProcessor.convert(p, 0, 0, mode, 100, false)),
          "full strength preserves old output");
      check(
          !Arrays.equals(
              ImageProcessor.convert(p, 0, 0, mode, 25, false),
              ImageProcessor.convert(p, 0, 0, mode, 100, false)),
          "strength changes gradient output");
      for (int amount : new int[] {0, 25, 50, 75, 100})
        for (int c : ImageProcessor.convert(p, 0, 0, mode, amount, false))
          check(c == 0xffffffff || c == 0xff000000, "strength retains palette");
      check(
          Arrays.equals(plain, ImageProcessor.convert(p, 0, 0, mode, -1, false)),
          "strength clamps below zero");
      check(
          Arrays.equals(
              ImageProcessor.convert(p, 0, 0, mode, 100, false),
              ImageProcessor.convert(p, 0, 0, mode, 101, false)),
          "strength clamps above 100");
    }
    check(
        Arrays.equals(plain, ImageProcessor.convert(p, 0, 0, 0, 50, false)),
        "disabled mode ignores strength");
    System.out.println("PASS: dither strength zero/full/intermediate/clamps and palette");
    check(count > 0, "dither");
    check(Wire.crc("123456789".getBytes(), 9) == 0xcbf43926L, "crc32 standard vector");
    byte[] req = Wire.packet(2, 0x1234, 0x89abcdefL, 44, new byte[] {1, 2, 3});
    check(
        Wire.u16(req, 6) == 0x1234
            && Wire.u32(req, 8) == 0x89abcdefL
            && Wire.u16(req, 12) == 44
            && req[14] == 3,
        "packet fields");
    check(Wire.crc(req, 60) == Wire.u32(req, 60), "packet crc");
    System.out.println(
        "PASS: palette, native orientation/corners, plane polarity, dithering, CRC32 and wire"
            + " layout");
  }
}
