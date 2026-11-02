package io.github.nannxi.epaper;

import java.util.TimeZone;

/** EPD1 opcode 06 payload. Capture phone time after tag identity is verified. */
public final class ClockConfig {
  public static final int OP_CLOCK = 6;
  public static final int FULL_EVERY_MINUTE = 0, PARTIAL_PERIODIC_FULL = 1;
  private ClockConfig() {}
  public static byte[] payload(long epochMillis, int offsetMinutes, int policy, int fullHours) {
    return payload(epochMillis, offsetMinutes, policy, fullHours, 0, 360);
  }
  public static byte[] payload(long epochMillis, int offsetMinutes, int policy, int fullHours, int sleepStart, int sleepEnd) {
    if (epochMillis < 0 || epochMillis / 1000L > 0xffffffffL || offsetMinutes < -840 || offsetMinutes > 840
        || policy < 0 || policy > 1 || fullHours < 1 || fullHours > 24
        || sleepStart < 0 || sleepStart >= 1440 || sleepEnd < 0 || sleepEnd >= 1440)
      throw new IllegalArgumentException("Invalid clock configuration");
    byte[] p = new byte[20];
    p[0] = 1; p[1] = (byte) policy; p[2] = (byte) fullHours;
    Wire.put32(p, 4, epochMillis / 1000L);
    Wire.put16(p, 8, offsetMinutes);
    Wire.put16(p, 10, (int) (epochMillis % 1000L));
    Wire.put16(p, 12, sleepStart);
    Wire.put16(p, 14, sleepEnd);
    return p;
  }
  public static byte[] now(int policy, int fullHours) {
    return now(policy, fullHours, 0, 360);
  }
  public static byte[] now(int policy, int fullHours, int sleepStart, int sleepEnd) {
    long now = System.currentTimeMillis();
    return payload(now, TimeZone.getDefault().getOffset(now) / 60000, policy, fullHours, sleepStart, sleepEnd);
  }
}
