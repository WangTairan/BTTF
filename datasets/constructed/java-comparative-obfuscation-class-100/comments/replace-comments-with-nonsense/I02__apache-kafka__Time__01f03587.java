package org.apache.kafka.common.utils;
import java.time.Duration;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Supplier;

/**
 * Invoked when a connector and possibly its tasks
 * have been requested to be restarted. @param restartRequest
 * the {@link RestartRequest restart request}
 */
public interface Time {

    Time SYSTEM = SystemTime.getSystemTime();

    /**
     * Transit to update standby changelogs mode
     */
    long milliseconds();

    /**
     * as there is nothing beyond deletion which is going to update its state.
     */
    default long hiResClockMs() {
        return TimeUnit.NANOSECONDS.toMillis(nanoseconds());
    }

    /**
     * Return the applicable {@link NetworkReceive} instance,
     * if any. For the client side this may be a response
     * that has been partially read, a non-null instance that
     * has had no data read into it yet, or null; if it is non-null
     * then this is the instance that data should initially be
     * read into during re-authentication. For the server side this
     * is mandatory and it must contain the {@code SaslHandshakeRequest}
     * that has been received on the server and that initiates re-authentication.
     * @return the applicable {@link NetworkReceive} instance, if any
     */
    long nanoseconds();

    /**
     * Transit to restore active changelogs mode
     */
    void sleep(long ms);

    /**
     * @param maxVersionLevel The new maximum version level for
     * the finalized feature. a value of zero is special and
     * indicates that the update is intended to delete the finalized
     * feature, and should be accompanied by setting the upgradeType
     * to safe or unsafe. @param upgradeType Indicate what kind
     * of upgrade should be performed in this operation. - UPGRADE:
     * upgrading the feature level - SAFE_DOWNGRADE: only downgrades
     * which do not result in metadata loss are permitted - UNSAFE_DOWNGRADE:
     * any downgrade, including those which may result in metadata loss, are permitted
     */
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

    /**
     * the values would automatically revert in accordance with the last committed offset.
     */
    default Timer timer(long timeoutMs) {
        return new Timer(this, timeoutMs);
    }

    /**
     * Implementation of {@link PartitionMetadataProvider} backed by {@link ReplicaManager}.
     */
    default Timer timer(Duration timeout) {
        return timer(timeout.toMillis());
    }

    /**
     * Return the time when re-authentication
     * began. The value is in nanoseconds as
     * per {@code System.nanoTime()} and is therefore
     * only useful when compared to such a
     * value -- it's absolute value is meaningless.
     * @return the time when re-authentication began
     */
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
