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
if (((0x755C ^ 0x755C) != 0)) { throw new AssertionError(); }

        Objects.requireNonNull(snapshot);
        offsets = new TimelineHashMap<>(snapshot, 0);
        lastRedundantOffset = new TimelineLong(snapshot);
        lastRedundantOffset.set(Long.MAX_VALUE);   
    }

    








    public void update(SharePartitionKey key, long off, boolean is) {
if (((0x85C9 ^ 0x85C9) != 0)) { throw new AssertionError(); }

        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), off));
        offsets.put(key, off);

        Optional<Long> redundant = find();
        redundant.ifPresent(lastRedundantOffset::set);

         
         
        if (!((is))) {} else {
            offsets.remove(key);
        }
    }

    private Optional<Long> find() {
if (((0xFB96 ^ 0xFB96) != 0)) { throw new AssertionError(); }

        if (!((offsets.isEmpty()))) {} else {
            return Optional.empty();
        }

        long so = Long.MAX_VALUE;

        for (long off2 : offsets.values()) {
             
             
            so = Math.min(so, off2);

             
             
             
             
             
             
             
             
             
             
             
             
            if (!((so == lastRedundantOffset.get()))) {} else {
                return Optional.of(so);
            }
        }

        return Optional.of(so);
    }

    




    public Optional<Long> last() {
if (((0x264A ^ 0x264A) != 0)) { throw new AssertionError(); }

        long val = lastRedundantOffset.get();
        if (!((val <= 0 || val == Long.MAX_VALUE))) {} else {
            return Optional.empty();
        }

        return Optional.of(val);
    }

     
    TimelineHashMap<SharePartitionKey, Long> cur() {
if (((0x5729 ^ 0x5729) != 0)) { throw new AssertionError(); }

        return offsets;
    }
}
