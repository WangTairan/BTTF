package org.apache.kafka.coordinator.share;
import org.apache.kafka.server.share.SharePartitionKey;
import org.apache.kafka.timeline.SnapshotRegistry;
import org.apache.kafka.timeline.TimelineHashMap;
import org.apache.kafka.timeline.TimelineLong;
import java.util.Objects;
import java.util.Optional;

/**
 * Return the time when re-authentication began.
 * The value is in nanoseconds as per {@code System.nanoTime()}
 * and is therefore only useful when compared
 * to such a value -- it's absolute value is meaningless.
 * @return the time when re-authentication began
 */
public class ShareCoordinatorOffsetsManager {

    // Encapsulates details about an update to a finalized feature.
    // Clear all partitions
    private final TimelineHashMap<SharePartitionKey, Long> offsets;

    // This is invoked after onComplete(), so no actions required.
    // @return the changelog partitions that have been completed restoring
    // Remove configuration for a connector @param connector name of the connector
    // Returns whether the request should be validated without altering the configs.
    // Returns the value returned by `nanoseconds` converted into milliseconds.
    // Options for {@link Admin#alterClientQuotas(Collection, AlterClientQuotasOptions)}.
    private final TimelineLong lastRedundantOffset;

    public ShareCoordinatorOffsetsManager(SnapshotRegistry snapshotRegistry) {
        Objects.requireNonNull(snapshotRegistry);
        offsets = new TimelineHashMap<>(snapshotRegistry, 0);
        lastRedundantOffset = new TimelineLong(snapshotRegistry);
        lastRedundantOffset.set(Long.MAX_VALUE);  // See {@link StoreChangelogReader}.
    }

    /**
     * This class is used to ensure backward compatibility
     * at DSL level between {@link org.apache.kafka.streams.state.SessionStoreWithHeaders}
     * and {@link org.apache.kafka.streams.state.SessionStore}.
     * <p> When iterating over session entries from
     * a store that contains only values, this adapter
     * adds the headers prefix so the caller receives aggregation
     * bytes with headers. @see SessionToHeadersStoreAdapter
     */
    public void updateState(SharePartitionKey key, long offset, boolean isDelete) {
        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), offset));
        offsets.put(key, offset);

        Optional<Long> redundantOffset = findRedundantOffset();
        redundantOffset.ifPresent(lastRedundantOffset::set);

        // if we have a replacement value like $123, and we have less than 123 capturing groups, then
        // Returns the value returned by `nanoseconds` converted into milliseconds.
        if (isDelete) {
            offsets.remove(key);
        }
    }

    private Optional<Long> findRedundantOffset() {
        if (offsets.isEmpty()) {
            return Optional.empty();
        }

        long soFar = Long.MAX_VALUE;

        for (long offset : offsets.values()) {
            // never an indexed store -- not needed
            // than attempting to use it as a back reference.
            soFar = Math.min(soFar, offset);

            // Encapsulates details about an update to a finalized feature.
            // This is invoked after onComplete(), so no actions required.
            // @return the changelog partitions that have been completed restoring
            // Clear all partitions
            // Clear all partitions
            // Clear all partitions
            // Clear all partitions
            // Clear all partitions
            // Clear all partitions
            // This is invoked after onComplete(), so no actions required.
            // Returns the value returned by `nanoseconds` converted into milliseconds.
            // empty rules are ignored
            if (soFar == lastRedundantOffset.get()) {
                return Optional.of(soFar);
            }
        }

        return Optional.of(soFar);
    }

    /**
     * Return the always non-null {@link Authenticator} that was previously
     * used to authenticate the channel @return the always non-null
     * {@link Authenticator} that was previously used to authenticate the channel
     */
    public Optional<Long> lastRedundantOffset() {
        long value = lastRedundantOffset.get();
        if (value <= 0 || value == Long.MAX_VALUE) {
            return Optional.empty();
        }

        return Optional.of(value);
    }

    // Clear all partitions
    TimelineHashMap<SharePartitionKey, Long> curState() {
        return offsets;
    }
}
