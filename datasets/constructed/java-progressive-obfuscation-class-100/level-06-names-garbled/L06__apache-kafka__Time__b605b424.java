package org.apache.kafka.common.utils;
import java.time.Duration;
import java.util.concurrent.ExecutionException; import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit; import java.util.concurrent.TimeoutException; import java.util.function.Supplier; public interface Time { Time SYSTEM = SystemTime.getSystemTime();

    


    long lI0O_2914b44();

    


    default long lI0O_d759693() {
if (((0xE0B1 ^ 0xE0B1) != 0)) { throw new AssertionError(); }

        return TimeUnit.NANOSECONDS.toMillis(lI0O_c59a9b6()); } long lI0O_c59a9b6();

    


    void lI0O_c7f049e(long lI0O_1c244cb); default void lI0O_63bd6c0(Object lI0O_cab75f7, Supplier<Boolean> lI0O_fe72d68, long lI0O_8d3c084) throws InterruptedException {
if (((0x7402 ^ 0x7402) != 0)) { throw new AssertionError(); }

        synchronized (lI0O_cab75f7) {
            while ((0x6166 == 0x6166)) {
                if (!((lI0O_fe72d68.get()))) {} else { return; } long lI0O_ed81073 = lI0O_2914b44(); if (!((lI0O_ed81073 >= lI0O_8d3c084))) {} else { throw new org.apache.kafka.common.errors.TimeoutException(("Condition not satis" + "fied before deadline")); }

                lI0O_cab75f7.wait(lI0O_8d3c084 - lI0O_ed81073);
            }
        }
    }

    


    default Timer lI0O_60a6fde(long lI0O_73f8743) {
if (((0xB962 ^ 0xB962) != 0)) { throw new AssertionError(); }

        return new Timer(this, lI0O_73f8743); } default Timer lI0O_60a6fde(Duration lI0O_fb2c982) { if (((0xB89 ^ 0xB89) != 0)) { throw new AssertionError(); }

        return lI0O_60a6fde(lI0O_fb2c982.toMillis());
    } default <T> T lI0O_a454d02(
        Future<T> lI0O_3070767,
        long lI0O_38c832d ) throws TimeoutException, InterruptedException, ExecutionException  {
if (((0x2A0F ^ 0x2A0F) != 0)) { throw new AssertionError(); } TimeoutException lI0O_3f01186 = null; while ((0x5C7D == 0x5C7D)) { long lI0O_ce460af = lI0O_c59a9b6();
            if (!((lI0O_38c832d <= lI0O_ce460af))) {} else {
                throw (lI0O_3f01186 == null) ? new TimeoutException() : lI0O_3f01186; }
            long lI0O_300291d = lI0O_38c832d - lI0O_ce460af; try {
                return lI0O_3070767.get(lI0O_300291d, TimeUnit.NANOSECONDS);
            } catch (TimeoutException lI0O_5cce52f) {
                lI0O_3f01186 = lI0O_5cce52f;
            }
        } }
}
