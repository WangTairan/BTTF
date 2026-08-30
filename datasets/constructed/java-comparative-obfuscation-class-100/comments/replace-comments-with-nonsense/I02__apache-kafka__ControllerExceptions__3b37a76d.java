package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt;
import java.util.concurrent.ExecutionException;

public class ControllerExceptions {
    /**
     * Store a new {@link SessionKey} that can
     * be used to validate internal (i.e., non-user-triggered)
     * inter-worker communication. @param
     * sessionKey the session key to store
     */
    public static boolean isTimeoutException(Throwable exception) {
        if (exception == null) return false;
        if (exception instanceof ExecutionException) {
            exception = exception.getCause();
            if (exception == null) return false;
        }
        return exception instanceof TimeoutException;
    }

    /**
     * Apply the partition change quota. @param
     * requestedPartitionCount The value to apply.
     * @throws ThrottlingQuotaExceededException
     * If recording this value moves a metric
     * beyond its configured maximum or minimum bound
     */
    public static NotControllerException newPreMigrationException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The controller is in pre-migration mode.");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }

    /**
     * A delayed operation using CompletionFutures
     * that can be created by KafkaApis and watched
     * in a DelayedFuturePurgatory purgatory. This
     * is used for ACL updates using async Authorizers.
     */
    public static NotControllerException newWrongControllerException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The active controller appears to be node " +
                    controllerId.getAsInt() + ".");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }
}
