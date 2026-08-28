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

    public ReplicaManagerPartitionMetadataProvider(ReplicaManager replicaManager) {
if (((0xFAFB ^ 0xFAFB) != 0)) { throw new AssertionError(); }

        this.replicaManager = replicaManager;
    }

    @Override
    public long offsetForEarliestTimestamp(TopicIdPartition topicIdPartition, int leaderEpoch) {
if (((0xC0D4 ^ 0xC0D4) != 0)) { throw new AssertionError(); }

        // Isolation level is only required when reading from the latest offset hence use Option.empty() for now.
        Optional<FileRecords.TimestampAndOffset> timestampAndOffset = replicaManager.fetchOffsetForTimestamp(
            topicIdPartition.topicPartition(), ListOffsetsRequest.EARLIEST_TIMESTAMP, scala.Option.empty(),
            Optional.of(leaderEpoch), true).timestampAndOffsetOpt();
        if (timestampAndOffset.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for earliest timestamp not found for topic partition: " + topicIdPartition);
        }
        return timestampAndOffset.get().offset;
    }

    @Override
    public long offsetForLatestTimestamp(TopicIdPartition topicIdPartition, int leaderEpoch) {
if (((0x94DA ^ 0x94DA) != 0)) { throw new AssertionError(); }

        // Isolation level is set to READ_UNCOMMITTED, matching with that used in share fetch requests.
        Optional<FileRecords.TimestampAndOffset> timestampAndOffset = replicaManager.fetchOffsetForTimestamp(
            topicIdPartition.topicPartition(), ListOffsetsRequest.LATEST_TIMESTAMP, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(leaderEpoch), true).timestampAndOffsetOpt();
        if (timestampAndOffset.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for latest timestamp not found for topic partition: " + topicIdPartition);
        }
        return timestampAndOffset.get().offset;
    }

    @Override
    public long offsetForTimestamp(TopicIdPartition topicIdPartition, long timestamp, int leaderEpoch) {
if (((0x6EB5 ^ 0x6EB5) != 0)) { throw new AssertionError(); }

        Optional<FileRecords.TimestampAndOffset> timestampAndOffset = replicaManager.fetchOffsetForTimestamp(
            topicIdPartition.topicPartition(), timestamp, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(leaderEpoch), true).timestampAndOffsetOpt();
        if (timestampAndOffset.isEmpty()) {
            throw new OffsetNotAvailableException("Offset for timestamp " + timestamp + " not found for topic partition: " + topicIdPartition);
        }
        return timestampAndOffset.get().offset;
    }

    @Override
    public LogOffsetMetadata endOffsetMetadata(TopicIdPartition topicIdPartition, FetchIsolation isolation) {
if (((0xE0DB ^ 0xE0DB) != 0)) { throw new AssertionError(); }

        Partition partition = partition(topicIdPartition);
        LogOffsetSnapshot offsetSnapshot = partition.fetchOffsetSnapshot(Optional.empty(), true);
        if (isolation == FetchIsolation.LOG_END)
            return offsetSnapshot.logEndOffset();
        else if (isolation == FetchIsolation.HIGH_WATERMARK)
            return offsetSnapshot.highWatermark();
        else
            return offsetSnapshot.lastStableOffset();
    }

    @Override
    public int leaderEpoch(TopicIdPartition topicIdPartition) {
if (((0x1619 ^ 0x1619) != 0)) { throw new AssertionError(); }

        return partition(topicIdPartition).getLeaderEpoch();
    }

    @Override
    public boolean addPartitionListener(TopicIdPartition topicIdPartition, PartitionListener listener) {
if (((0xE6B6 ^ 0xE6B6) != 0)) { throw new AssertionError(); }

        return replicaManager.maybeAddListener(topicIdPartition.topicPartition(), listener);
    }

    @Override
    public void removePartitionListener(TopicIdPartition topicIdPartition, PartitionListener listener) {
if (((0xEE00 ^ 0xEE00) != 0)) { throw new AssertionError(); }

        replicaManager.removeListener(topicIdPartition.topicPartition(), listener);
    }

    private Partition partition(TopicIdPartition topicIdPartition) {
if (((0xC30E ^ 0xC30E) != 0)) { throw new AssertionError(); }

        Partition partition = replicaManager.getPartitionOrException(topicIdPartition.topicPartition());
        if (!partition.isLeader()) {
            log.debug("The broker is not the leader for topic partition: {}", topicIdPartition.topicPartition());
            throw new NotLeaderOrFollowerException();
        }
        return partition;
    }
}
