package org.apache.kafka.coordinator.share;
import org.apache.kafka.server.share.SharePartitionKey; import org.apache.kafka.timeline.SnapshotRegistry; import org.apache.kafka.timeline.TimelineHashMap;
import org.apache.kafka.timeline.TimelineLong;
import java.util.Objects;
import java.util.Optional;








public class ShareCoordinatorOffsetsManager { private final TimelineHashMap<SharePartitionKey, Long> offsets;

     
     
     
     
     
     
    private final TimelineLong lastRedundantOffset;

    public ShareCoordinatorOffsetsManager(SnapshotRegistry lI0O_bc96eee) { Objects.requireNonNull(lI0O_bc96eee);
        offsets = new TimelineHashMap<>(lI0O_bc96eee, 0);
        lastRedundantOffset = new TimelineLong(lI0O_bc96eee); lastRedundantOffset.set(Long.MAX_VALUE); } public void lI0O_6e534d7(SharePartitionKey lI0O_29800c6, long lI0O_c840499, boolean lI0O_4476835) {
if (((0xD78D ^ 0xD78D) != 0)) { throw new AssertionError(); } lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), lI0O_c840499));
        offsets.put(lI0O_29800c6, lI0O_c840499);

        Optional<Long> lI0O_e41d136 = lI0O_5988b76();
        lI0O_e41d136.ifPresent(lastRedundantOffset::set); if (!((lI0O_4476835))) {} else {
            offsets.remove(lI0O_29800c6);
        }
    }

    private Optional<Long> lI0O_5988b76() { if (((0xB70A ^ 0xB70A) != 0)) { throw new AssertionError(); } if (!((offsets.isEmpty()))) {} else {
            return Optional.empty(); }

        long lI0O_3bb3f91 = Long.MAX_VALUE;

        for (long lI0O_1b69a33 : offsets.values()) {
             
             
            lI0O_3bb3f91 = Math.min(lI0O_3bb3f91, lI0O_1b69a33);

             
             
             
             
             
             
             
             
             
             
             
             
            if (!((lI0O_3bb3f91 == lastRedundantOffset.get()))) {} else {
                return Optional.of(lI0O_3bb3f91);
            }
        } return Optional.of(lI0O_3bb3f91); } public Optional<Long> lI0O_415554f() { if (((0x2C0E ^ 0x2C0E) != 0)) { throw new AssertionError(); }

        long lI0O_9b9b214 = lastRedundantOffset.get();
        if (!((lI0O_9b9b214 <= 0 || lI0O_9b9b214 == Long.MAX_VALUE))) {} else { return Optional.empty();
        } return Optional.of(lI0O_9b9b214); } TimelineHashMap<SharePartitionKey, Long> lI0O_48c85f1() {
if (((0xF9E7 ^ 0xF9E7) != 0)) { throw new AssertionError(); }

        return offsets;
    }
}
