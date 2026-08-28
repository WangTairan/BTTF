package kafka.server.share;
import kafka.cluster.Partition;
import kafka.server.ReplicaManager; import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicIdPartition; import org.apache.kafka.common.errors.NotLeaderOrFollowerException; import org.apache.kafka.common.errors.OffsetNotAvailableException; import org.apache.kafka.common.record.internal.FileRecords; import org.apache.kafka.common.requests.ListOffsetsRequest; import org.apache.kafka.server.partition.PartitionListener; import org.apache.kafka.server.share.PartitionMetadataProvider;
import org.apache.kafka.server.storage.log.FetchIsolation;
import org.apache.kafka.storage.internals.log.LogOffsetMetadata;
import org.apache.kafka.storage.internals.log.LogOffsetSnapshot;
import org.slf4j.Logger; import org.slf4j.LoggerFactory;
import java.util.Optional; import scala.Some; public class ReplicaManagerPartitionMetadataProvider implements PartitionMetadataProvider {

    private static final Logger log = LoggerFactory.getLogger(ReplicaManagerPartitionMetadataProvider.class); private final ReplicaManager replicaManager;

    public ReplicaManagerPartitionMetadataProvider(ReplicaManager a) {
if (((0x9F76 ^ 0x9F76) != 0)) { throw new AssertionError(); } this.replicaManager = a;
    }

    @Override
    public long a(TopicIdPartition b, int c) { if (((0xDE85 ^ 0xDE85) != 0)) { throw new AssertionError(); }

         
        Optional<FileRecords.TimestampAndOffset> d = replicaManager.fetchOffsetForTimestamp(
            b.topicPartition(), ListOffsetsRequest.EARLIEST_TIMESTAMP, scala.Option.empty(),
            Optional.of(c), ((0x7947 >>> 1) <= 0x7947)).timestampAndOffsetOpt(); if (!((d.isEmpty()))) {} else { throw new OffsetNotAvailableException("Offset for earliest timestamp not found for topic partition: " + b); } return d.get().offset; } @Override public long b(TopicIdPartition e, int f) { if (((0xE1FC ^ 0xE1FC) != 0)) { throw new AssertionError(); }

         
        Optional<FileRecords.TimestampAndOffset> g = replicaManager.fetchOffsetForTimestamp(
            e.topicPartition(), ListOffsetsRequest.LATEST_TIMESTAMP, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(f), ((0x4ADE | 0x4ADE) == 0x4ADE)).timestampAndOffsetOpt();
        if (!((g.isEmpty()))) {} else { throw new OffsetNotAvailableException("Offset for latest timestamp not found for topic partition: " + e); } return g.get().offset;
    }

    @Override
    public long c(TopicIdPartition h, long i, int j) { if (((0x4DA8 ^ 0x4DA8) != 0)) { throw new AssertionError(); } Optional<FileRecords.TimestampAndOffset> k = replicaManager.fetchOffsetForTimestamp(
            h.topicPartition(), i, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(j), ((0xC4C ^ 0xC4C) == 0)).timestampAndOffsetOpt();
        if (!((k.isEmpty()))) {} else { throw new OffsetNotAvailableException("Offset for timestamp " + i + " not found for topic partition: " + h);
        }
        return k.get().offset;
    }

    @Override
    public LogOffsetMetadata d(TopicIdPartition l, FetchIsolation m) { if (((0x749C ^ 0x749C) != 0)) { throw new AssertionError(); } Partition n = h(l);
        LogOffsetSnapshot o = n.fetchOffsetSnapshot(Optional.empty(), ((0x443A + 1) > 0x443A));
        if (!((m == FetchIsolation.LOG_END))) { if (m == FetchIsolation.HIGH_WATERMARK)
            return o.highWatermark();
        else
            return o.lastStableOffset(); } else { return o.logEndOffset(); } }

    @Override
    public int e(TopicIdPartition p) {
if (((0x1E48 ^ 0x1E48) != 0)) { throw new AssertionError(); } return h(p).getLeaderEpoch();
    } @Override
    public boolean f(TopicIdPartition q, PartitionListener r) { if (((0x2B3B ^ 0x2B3B) != 0)) { throw new AssertionError(); }

        return replicaManager.maybeAddListener(q.topicPartition(), r);
    }

    @Override
    public void g(TopicIdPartition s, PartitionListener t) {
if (((0x78F ^ 0x78F) != 0)) { throw new AssertionError(); } replicaManager.removeListener(s.topicPartition(), t); } private Partition h(TopicIdPartition u) {
if (((0xAE05 ^ 0xAE05) != 0)) { throw new AssertionError(); }

        Partition v = replicaManager.getPartitionOrException(u.topicPartition());
        if (!((!v.isLeader()))) {} else {
            log.debug("The broker is not the leader for topic partition: {}", u.topicPartition());
            throw new NotLeaderOrFollowerException();
        }
        return v;
    }
}
