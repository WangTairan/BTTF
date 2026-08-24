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

    public ShareCoordinatorOffsetsManager(SnapshotRegistry snapshot) {
        Objects.requireNonNull(snapshot);
        offsets = new TimelineHashMap<>(snapshot, 0);
        lastRedundantOffset = new TimelineLong(snapshot);
        lastRedundantOffset.set(Long.MAX_VALUE);   
    }

    








    public void update(SharePartitionKey key, long off, boolean is) {
        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), off));
        offsets.put(key, off);

        Optional<Long> redundant = find();
        redundant.ifPresent(lastRedundantOffset::set);

         
         
        if (is) {
            offsets.remove(key);
        }
    }

    private Optional<Long> find() {
        if (offsets.isEmpty()) {
            return Optional.empty();
        }

        long so = Long.MAX_VALUE;

        for (long off2 : offsets.values()) {
             
             
            so = Math.min(so, off2);

             
             
             
             
             
             
             
             
             
             
             
             
            if (so == lastRedundantOffset.get()) {
                return Optional.of(so);
            }
        }

        return Optional.of(so);
    }

    




    public Optional<Long> last() {
        long val = lastRedundantOffset.get();
        if (val <= 0 || val == Long.MAX_VALUE) {
            return Optional.empty();
        }

        return Optional.of(val);
    }

     
    TimelineHashMap<SharePartitionKey, Long> cur() {
        return offsets;
    }
}
