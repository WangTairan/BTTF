package org.apache.kafka.coordinator.share;
import org.apache.kafka.server.share.SharePartitionKey;
import org.apache.kafka.timeline.SnapshotRegistry;
import org.apache.kafka.timeline.TimelineHashMap;
import org.apache.kafka.timeline.TimelineLong;
import java.util.Objects;
import java.util.Optional;








public class ShareCoordinatorOffsetsManager {

     
     
    private final TimelineHashMap<SharePartitionKey, Long> offsets;

     
     
     
     
     
     
    private final TimelineLong lastRedundantOffset;

    public ShareCoordinatorOffsetsManager(SnapshotRegistry snapshotRegistry) {
        Objects.requireNonNull(snapshotRegistry);
        offsets = new TimelineHashMap<>(snapshotRegistry, 0);
        lastRedundantOffset = new TimelineLong(snapshotRegistry);
        lastRedundantOffset.set(Long.MAX_VALUE);   
    }

    








    public void updateState(SharePartitionKey key, long offset, boolean isDelete) {
        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), offset));
        offsets.put(key, offset);

        Optional<Long> redundantOffset = findRedundantOffset();
        redundantOffset.ifPresent(lastRedundantOffset::set);

         
         
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
             
             
            soFar = Math.min(soFar, offset);

             
             
             
             
             
             
             
             
             
             
             
             
            if (soFar == lastRedundantOffset.get()) {
                return Optional.of(soFar);
            }
        }

        return Optional.of(soFar);
    }

    




    public Optional<Long> lastRedundantOffset() {
        long value = lastRedundantOffset.get();
        if (value <= 0 || value == Long.MAX_VALUE) {
            return Optional.empty();
        }

        return Optional.of(value);
    }

     
    TimelineHashMap<SharePartitionKey, Long> curState() {
        return offsets;
    }
}
