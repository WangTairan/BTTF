package org.apache.kafka.common.utils;
import java.time.Duration;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;






public interface Time {

    Time SYSTEM = SystemTime.getSystemTime();

    


    long milliseconds();

    


    default long hiResClockMs() {
        return TimeUnit.NANOSECONDS.toMillis(nanoseconds());
    }

    










    long nanoseconds();

    


    void sleep(long ms);

    










    default void waitObject(Object obj, Supplier<Boolean> condition, long deadlineMs) throws InterruptedException {
        synchronized (obj) {
            while (true) {
                if (condition.get())
                    return;

                long currentTimeMs = milliseconds();
                if (currentTimeMs >= deadlineMs)
                    throw new org.apache.kafka.common.errors.TimeoutException("Condition not satisfied before deadline");

                obj.wait(deadlineMs - currentTimeMs);
            }
        }
    }

    


    default Timer timer(long timeoutMs) {
        return new Timer(this, timeoutMs);
    }

    


    default Timer timer(Duration timeout) {
        return timer(timeout.toMillis());
    }

    







    default <T> T waitForFuture(
        Future<T> future,
        long deadlineNs
    ) throws TimeoutException, InterruptedException, ExecutionException  {
        TimeoutException timeoutException = null;
        while (true) {
            long nowNs = nanoseconds();
            if (deadlineNs <= nowNs) {
                throw (timeoutException == null) ? new TimeoutException() : timeoutException;
            }
            long deltaNs = deadlineNs - nowNs;
            try {
                return future.get(deltaNs, TimeUnit.NANOSECONDS);
            } catch (TimeoutException t) {
                timeoutException = t;
            }
        }
    }
}
