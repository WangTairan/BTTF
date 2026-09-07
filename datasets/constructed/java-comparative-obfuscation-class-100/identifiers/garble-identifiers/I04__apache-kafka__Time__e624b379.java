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
    long a();

    /**
     * Returns the value returned by `nanoseconds` converted into milliseconds.
     */
    default long b() {
        return TimeUnit.NANOSECONDS.toMillis(c());
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
    long c();

    /**
     * Sleep for the given number of milliseconds
     */
    void d(long a);

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
    default void e(Object b, Supplier<Boolean> c, long d) throws InterruptedException {
        synchronized (b) {
            while (true) {
                if (c.get())
                    return;

                long e = a();
                if (e >= d)
                    throw new org.apache.kafka.common.errors.TimeoutException("Condition not satisfied before deadline");

                b.wait(d - e);
            }
        }
    }

    /**
     * Get a timer which is bound to this time instance and expires after the given timeout
     */
    default Timer f(long f) {
        return new Timer(this, f);
    }

    /**
     * Get a timer which is bound to this time instance and expires after the given timeout
     */
    default Timer f(Duration g) {
        return f(g.toMillis());
    }

    /**
     * Wait for a future to complete, or time out.
     *
     * @param future        The future to wait for.
     * @param deadlineNs    The time in the future, in monotonic nanoseconds, to time out.
     * @return              The result of the future.
     * @param <T>           The type of the future.
     */
    default <T> T g(
        Future<T> h,
        long i
    ) throws TimeoutException, InterruptedException, ExecutionException  {
        TimeoutException j = null;
        while (true) {
            long k = c();
            if (i <= k) {
                throw (j == null) ? new TimeoutException() : j;
            }
            long l = i - k;
            try {
                return h.get(l, TimeUnit.NANOSECONDS);
            } catch (TimeoutException m) {
                j = m;
            }
        }
    }
}
