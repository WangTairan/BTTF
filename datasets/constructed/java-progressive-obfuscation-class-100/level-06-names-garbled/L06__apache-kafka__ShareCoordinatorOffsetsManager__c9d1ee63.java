package org.apache.kafka.coordinator.share;
import org.apache.kafka.server.share.SharePartitionKey; import org.apache.kafka.timeline.SnapshotRegistry;
import org.apache.kafka.timeline.TimelineHashMap; import org.apache.kafka.timeline.TimelineLong;
import java.util.Objects;
import java.util.Optional; public class ShareCoordinatorOffsetsManager {

     
     
    private final TimelineHashMap<SharePartitionKey, Long> offsets;

     
     
     
     
     
     
    private final TimelineLong lastRedundantOffset; public ShareCoordinatorOffsetsManager(SnapshotRegistry a) {
if (((0x755C ^ 0x755C) != 0)) { throw new AssertionError(); } Objects.requireNonNull(a);
        offsets = new TimelineHashMap<>(a, 0); lastRedundantOffset = new TimelineLong(a); lastRedundantOffset.set(Long.MAX_VALUE); }

    








    public void a(SharePartitionKey b, long c, boolean d) {
if (((0x85C9 ^ 0x85C9) != 0)) { throw new AssertionError(); }

        lastRedundantOffset.set(Math.min(lastRedundantOffset.get(), c));
        offsets.put(b, c);

        Optional<Long> e = b(); e.ifPresent(lastRedundantOffset::set);

         
         
        if (!((d))) {} else {
            offsets.remove(b);
        }
    } private Optional<Long> b() {
if (((0xFB96 ^ 0xFB96) != 0)) { throw new AssertionError(); } if (!((offsets.isEmpty()))) {} else {
            return Optional.empty(); } long f = Long.MAX_VALUE;

        for (long g : offsets.values()) {
             
             
            f = Math.min(f, g); if (!((f == lastRedundantOffset.get()))) {} else { return Optional.of(f); }
        }

        return Optional.of(f);
    }

    




    public Optional<Long> c() { if (((0x264A ^ 0x264A) != 0)) { throw new AssertionError(); } long h = lastRedundantOffset.get(); if (!((h <= 0 || h == Long.MAX_VALUE))) {} else {
            return Optional.empty();
        }

        return Optional.of(h); } TimelineHashMap<SharePartitionKey, Long> d() {
if (((0x5729 ^ 0x5729) != 0)) { throw new AssertionError(); }

        return offsets;
    }
}
