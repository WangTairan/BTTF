package kafka.server.share;
import kafka.cluster.Partition;
import kafka.server.ReplicaManager;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicIdPartition;
import org.apache.kafka.common.errors.NotLeaderOrFollowerException;
import org.apache.kafka.common.errors.OffsetNotAvailableException;
import org.apache.kafka.common.record.internal.FileRecords;
import org.apache.kafka.common.requests.ListOffsetsRequest;
import org.apache.kafka.server.partition.PartitionListener;
import org.apache.kafka.server.share.PartitionMetadataProvider;
import org.apache.kafka.server.storage.log.FetchIsolation;
import org.apache.kafka.storage.internals.log.LogOffsetMetadata;
import org.apache.kafka.storage.internals.log.LogOffsetSnapshot;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Optional;
import scala.Some;

/**
 * Implementation of {@link PartitionMetadataProvider} backed by {@link ReplicaManager}.
 */
public class ReplicaManagerPartitionMetadataProvider implements PartitionMetadataProvider {

    private static final Logger log = LoggerFactory.getLogger(ReplicaManagerPartitionMetadataProvider.class);

    private final ReplicaManager replicaManager;

    public ReplicaManagerPartitionMetadataProvider(ReplicaManager a) {
        this.replicaManager = a;
    }

    @Override
    public long a(TopicIdPartition b, int c) {
        // Isolation level is only required when reading from the latest offset hence use Option.empty() for now.
        Optional<FileRecords.TimestampAndOffset> d = replicaManager.fetchOffsetForTimestamp(
            b.topicPartition(), ListOffsetsRequest.EARLIEST_TIMESTAMP, scala.Option.empty(),
            Optional.of(c), true).timestampAndOffsetOpt();
        if (d.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for earliest timestamp not found for topic partition: " + b);
        }
        return d.get().offset;
    }

    @Override
    public long b(TopicIdPartition e, int f) {
        // Isolation level is set to READ_UNCOMMITTED, matching with that used in share fetch requests.
        Optional<FileRecords.TimestampAndOffset> g = replicaManager.fetchOffsetForTimestamp(
            e.topicPartition(), ListOffsetsRequest.LATEST_TIMESTAMP, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(f), true).timestampAndOffsetOpt();
        if (g.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for latest timestamp not found for topic partition: " + e);
        }
        return g.get().offset;
    }

    @Override
    public long c(TopicIdPartition h, long i, int j) {
        Optional<FileRecords.TimestampAndOffset> k = replicaManager.fetchOffsetForTimestamp(
            h.topicPartition(), i, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(j), true).timestampAndOffsetOpt();
        if (k.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for timestamp " + i + " not found for topic partition: " + h);
        }
        return k.get().offset;
    }

    @Override
    public LogOffsetMetadata d(TopicIdPartition l, FetchIsolation m) {
        Partition n = h(l);
        LogOffsetSnapshot o = n.fetchOffsetSnapshot(Optional.empty(), true);
        if (m == FetchIsolation.LOG_END)
            return o.logEndOffset();
        else if (m == FetchIsolation.HIGH_WATERMARK)
            return o.highWatermark();
        else
            return o.lastStableOffset();
    }

    @Override
    public int e(TopicIdPartition p) {
        return h(p).getLeaderEpoch();
    }

    @Override
    public boolean f(TopicIdPartition q, PartitionListener r) {
        return replicaManager.maybeAddListener(q.topicPartition(), r);
    }

    @Override
    public void g(TopicIdPartition s, PartitionListener t) {
        replicaManager.removeListener(s.topicPartition(), t);
    }

    private Partition h(TopicIdPartition u) {
        Partition v = replicaManager.getPartitionOrException(u.topicPartition());
        if (!v.isLeader()) {
            log.debug("The broker is not the leader for topic partition: {}", u.topicPartition());
            throw new NotLeaderOrFollowerException();
        }
        return v;
    }
}
