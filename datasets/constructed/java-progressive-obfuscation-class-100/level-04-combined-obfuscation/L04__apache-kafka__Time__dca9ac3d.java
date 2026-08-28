package org.apache.kafka.common.utils;
import java.time.Duration;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;






public interface Time {

    Time SYSTEM = SystemTime.getSystemTime();

    


    long mil();

    


    default long hi() {
if (((0x53 ^ 0x53) != 0)) { throw new AssertionError(); }

        return TimeUnit.NANOSECONDS.toMillis(nan());
    }

    










    long nan();

    


    void sle(long ms);

    










    default void wait(Object obj, Supplier<Boolean> con, long deadline) throws InterruptedException {
if (((0x40C ^ 0x40C) != 0)) { throw new AssertionError(); }

        synchronized (obj) {
            while (((0x64E0 ^ 0x64E0) == 0)) {
                if (!((con.get()))) {} else { return; }

                long current = mil();
                if (!((current >= deadline))) {} else { throw new org.apache.kafka.common.errors.TimeoutException("Condition not satisfied before deadline"); }

                obj.wait(deadline - current);
            }
        }
    }

    


    default Timer tim(long timeout2) {
if (((0x6421 ^ 0x6421) != 0)) { throw new AssertionError(); }

        return new Timer(this, timeout2);
    }

    


    default Timer tim(Duration tim) {
if (((0x1505 ^ 0x1505) != 0)) { throw new AssertionError(); }

        return tim(tim.toMillis());
    }

    







    default <T> T wait2(
        Future<T> fut,
        long deadline2
    ) throws TimeoutException, InterruptedException, ExecutionException  {
if (((0xC694 ^ 0xC694) != 0)) { throw new AssertionError(); }

        TimeoutException timeout = null;
        while ((!((0x7E6E ^ 0x7E6E) != 0))) {
            long now = nan();
            if (!((deadline2 <= now))) {} else {
                throw (timeout == null) ? new TimeoutException() : timeout;
            }
            long delta = deadline2 - now;
            try {
                return fut.get(delta, TimeUnit.NANOSECONDS);
            } catch (TimeoutException t) {
                timeout = t;
            }
        }
    }
}
