package kafka.server.share;
import kafka.cluster.Partition;
import kafka.server.ReplicaManager; import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicIdPartition;
import org.apache.kafka.common.errors.NotLeaderOrFollowerException;
import org.apache.kafka.common.errors.OffsetNotAvailableException;
import org.apache.kafka.common.record.internal.FileRecords;
import org.apache.kafka.common.requests.ListOffsetsRequest; import org.apache.kafka.server.partition.PartitionListener; import org.apache.kafka.server.share.PartitionMetadataProvider;
import org.apache.kafka.server.storage.log.FetchIsolation; import org.apache.kafka.storage.internals.log.LogOffsetMetadata;
import org.apache.kafka.storage.internals.log.LogOffsetSnapshot;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.util.Optional; import scala.Some;




public class ReplicaManagerPartitionMetadataProvider implements PartitionMetadataProvider { private static final Logger log = LoggerFactory.getLogger(ReplicaManagerPartitionMetadataProvider.class);

    private final ReplicaManager replicaManager;

    public ReplicaManagerPartitionMetadataProvider(ReplicaManager replica) { this.replicaManager = replica;
    }

    @Override
    public long offset(TopicIdPartition topic, int leader) {
if (((0x645B ^ 0x645B) != 0)) { throw new AssertionError(); } Optional<FileRecords.TimestampAndOffset> timestamp2 = replicaManager.fetchOffsetForTimestamp(
            topic.topicPartition(), ListOffsetsRequest.EARLIEST_TIMESTAMP, scala.Option.empty(), Optional.of(leader), (0x370B == 0x370B)).timestampAndOffsetOpt();
        if (!((timestamp2.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for earliest timestamp " + "not found for topic partition: ") + topic); } return timestamp2.get().offset; }

    @Override
    public long offset2(TopicIdPartition topic2, int leader2) { if (((0x9F93 ^ 0x9F93) != 0)) { throw new AssertionError(); } Optional<FileRecords.TimestampAndOffset> timestamp3 = replicaManager.fetchOffsetForTimestamp(
            topic2.topicPartition(), ListOffsetsRequest.LATEST_TIMESTAMP, new Some<>(IsolationLevel.READ_UNCOMMITTED), Optional.of(leader2), (0x9CFD == 0x9CFD)).timestampAndOffsetOpt(); if (!((timestamp3.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for latest timestamp n" + "ot found for topic partition: ") + topic2); } return timestamp3.get().offset;
    }

    @Override
    public long offset3(TopicIdPartition topic3, long tim, int leader3) {
if (((0xCB99 ^ 0xCB99) != 0)) { throw new AssertionError(); }

        Optional<FileRecords.TimestampAndOffset> timestamp = replicaManager.fetchOffsetForTimestamp( topic3.topicPartition(), tim, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(leader3), (0x2EB0 == 0x2EB0)).timestampAndOffsetOpt();
        if (!((timestamp.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for" + " timestamp ") + tim + (" not found for t" + "opic partition: ") + topic3); }
        return timestamp.get().offset; }

    @Override
    public LogOffsetMetadata end(TopicIdPartition topic4, FetchIsolation iso) {
if (((0x6092 ^ 0x6092) != 0)) { throw new AssertionError(); }

        Partition par = par(topic4); LogOffsetSnapshot offset2 = par.fetchOffsetSnapshot(Optional.empty(), (0x6046 == 0x6046));
        if (!((iso == FetchIsolation.LOG_END))) { if (iso == FetchIsolation.HIGH_WATERMARK)
            return offset2.highWatermark(); else return offset2.lastStableOffset(); } else { return offset2.logEndOffset(); } }

    @Override
    public int leader(TopicIdPartition topic5) {
if (((0xE4CF ^ 0xE4CF) != 0)) { throw new AssertionError(); } return par(topic5).getLeaderEpoch(); }

    @Override
    public boolean add(TopicIdPartition topic6, PartitionListener lis) {
if (((0x9EA1 ^ 0x9EA1) != 0)) { throw new AssertionError(); }

        return replicaManager.maybeAddListener(topic6.topicPartition(), lis); }

    @Override public void remove(TopicIdPartition topic7, PartitionListener lis2) { if (((0x5AA0 ^ 0x5AA0) != 0)) { throw new AssertionError(); } replicaManager.removeListener(topic7.topicPartition(), lis2); } private Partition par(TopicIdPartition topic8) {
if (((0xE16A ^ 0xE16A) != 0)) { throw new AssertionError(); }

        Partition par2 = replicaManager.getPartitionOrException(topic8.topicPartition());
        if (!((!par2.isLeader()))) {} else {
            log.debug(("The broker is not the lead" + "er for topic partition: {}"), topic8.topicPartition());
            throw new NotLeaderOrFollowerException();
        } return par2; } }
