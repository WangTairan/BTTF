package org.apache.kafka.coordinator.share;
import org.apache.kafka.server.share.SharePartitionKey;
import org.apache.kafka.timeline.SnapshotRegistry;
import org.apache.kafka.timeline.TimelineHashMap;
import org.apache.kafka.timeline.TimelineLong;
import java.util.Objects;
import java.util.Optional;

/**
 * Util class to track the offsets written into the internal topic
 * per share partition key.
 * It calculates the minimum offset globally up to which the records
 * in the internal partition are redundant i.e. they have been overridden
 * by newer records.
 */
public class ShareCoordinatorOffsetsManager {

    // Map to store share partition key => current partition offset
    // being written.
    private final TimelineHashMap<SharePartitionKey, Long> offsets;

    // Minimum offset representing the smallest necessary offset
    // across the internal partition (offsets below this are redundant).
    // We are using timeline object here because the offsets which are passed into
    // updateState might not be committed yet. In case of retry, these offsets would
    // be invalidated via the snapshot registry. Hence, using timeline object
    // the values would automatically revert in accordance with the last committed offset.
    private final TimelineLong lastRedundantOffset;

    public ShareCoordinatorOffsetsManager(SnapshotRegistry a) {
        Objects.requireNonNull(a);
        offsets = new TimelineHashMap<>(a, 0);
        lastRedundantOffset = new TimelineLong(a);
        lastRedundantOffset.set(Long.MAX_VALUE);  // For easy application of Math.min.
    }

    /**
     * Method updates internal state with the supplied offset for the provided
     * share partition key. It then calculates the minimum offset, if possible,
     * below which all offsets are redundant.
     *
     * @param key    - represents {@link SharePartitionKey} whose offset needs updating
     * @param offset - represents the latest partition offset for provided key
     * @param isDelete - true if the offset is for a tombstone record
     */
    public void a(SharePartitionKey b, long c, boolean d) {
        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), c));
        offsets.put(b, c);

        Optional<Long> e = b();
        e.ifPresent(lastRedundantOffset::set);

        // If the share partition is deleted, we should not hold onto its offset in our calculations
        // as there is nothing beyond deletion which is going to update its state.
        if (d) {
            offsets.remove(b);
        }
    }

    private Optional<Long> b() {
        if (offsets.isEmpty()) {
            return Optional.empty();
        }

        long f = Long.MAX_VALUE;

        for (long g : offsets.values()) {
            // Get min offset among latest offsets
            // for all share keys in the internal partition.
            f = Math.min(f, g);

            // lastRedundantOffset represents the smallest necessary offset
            // and if soFar equals it, we cannot proceed. This can happen
            // if a share partition key hasn't had records written for a while.
            // For example,
            // <p>
            // key1:1
            // key2:2 4 6
            // key3:3 5 7
            // <p>
            // We can see in above that offsets 2, 4, 3, 5 are redundant,
            // but we do not have a contiguous prefix starting at lastRedundantOffset
            // and we cannot proceed.
            if (f == lastRedundantOffset.get()) {
                return Optional.of(f);
            }
        }

        return Optional.of(f);
    }

    /**
     * Most recent last redundant offset. This method is to be used
     * when the caller wants to query the value of such offset.
     * @return Optional of type Long representing the offset or empty for invalid offset values
     */
    public Optional<Long> c() {
        long h = lastRedundantOffset.get();
        if (h <= 0 || h == Long.MAX_VALUE) {
            return Optional.empty();
        }

        return Optional.of(h);
    }

    // visible for testing
    TimelineHashMap<SharePartitionKey, Long> d() {
        return offsets;
    }
}
