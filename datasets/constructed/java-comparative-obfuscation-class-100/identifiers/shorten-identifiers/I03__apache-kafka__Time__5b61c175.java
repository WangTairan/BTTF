package org.apache.kafka.common.utils;
import java.time.Duration;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;

/**
 * An interface abstracting the clock to use in unit testing classes that make use of clock time.
 *
 * Implementations of this class should be thread-safe.
 */
public interface Time {

    Time SYSTEM = SystemTime.getSystemTime();

    /**
     * Returns the current time in milliseconds.
     */
    long mil();

    /**
     * Returns the value returned by `nanoseconds` converted into milliseconds.
     */
    default long hi() {
        return TimeUnit.NANOSECONDS.toMillis(nan());
    }

    /**
     * Returns the current value of the running JVM's high-resolution time source, in nanoseconds.
     *
     * <p>This method can only be used to measure elapsed time and is
     * not related to any other notion of system or wall-clock time.
     * The value returned represents nanoseconds since some fixed but
     * arbitrary <i>origin</i> time (perhaps in the future, so values
     * may be negative).  The same origin is used by all invocations of
     * this method in an instance of a Java virtual machine; other
     * virtual machine instances are likely to use a different origin.
     */
    long nan();

    /**
     * Sleep for the given number of milliseconds
     */
    void sle(long ms);

    /**
     * Wait for a condition using the monitor of a given object. This avoids the implicit
     * dependence on system time when calling {@link Object#wait()}.
     *
     * @param obj The object that will be waited with {@link Object#wait()}. Note that it is the responsibility
     *      of the caller to call notify on this object when the condition is satisfied.
     * @param condition The condition we are awaiting
     * @param deadlineMs The deadline timestamp at which to raise a timeout error
     *
     * @throws org.apache.kafka.common.errors.TimeoutException if the timeout expires before the condition is satisfied
     */
    default void wait(Object obj, Supplier<Boolean> con, long deadline) throws InterruptedException {
        synchronized (obj) {
            while (true) {
                if (con.get())
                    return;

                long current = mil();
                if (current >= deadline)
                    throw new org.apache.kafka.common.errors.TimeoutException("Condition not satisfied before deadline");

                obj.wait(deadline - current);
            }
        }
    }

    /**
     * Get a timer which is bound to this time instance and expires after the given timeout
     */
    default Timer tim(long timeout2) {
        return new Timer(this, timeout2);
    }

    /**
     * Get a timer which is bound to this time instance and expires after the given timeout
     */
    default Timer tim(Duration tim) {
        return tim(tim.toMillis());
    }

    /**
     * Wait for a future to complete, or time out.
     *
     * @param future        The future to wait for.
     * @param deadlineNs    The time in the future, in monotonic nanoseconds, to time out.
     * @return              The result of the future.
     * @param <T>           The type of the future.
     */
    default <T> T wait2(
        Future<T> fut,
        long deadline2
    ) throws TimeoutException, InterruptedException, ExecutionException  {
        TimeoutException timeout = null;
        while (true) {
            long now = nan();
            if (deadline2 <= now) {
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
