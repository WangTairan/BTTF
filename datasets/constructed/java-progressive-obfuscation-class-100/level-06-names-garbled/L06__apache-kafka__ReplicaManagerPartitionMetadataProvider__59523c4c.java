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

    public ReplicaManagerPartitionMetadataProvider(ReplicaManager lI0O_ba05b0d) { this.replicaManager = lI0O_ba05b0d;
    }

    @Override
    public long lI0O_1db418e(TopicIdPartition lI0O_6fef693, int lI0O_ba2357e) {
if (((0x645B ^ 0x645B) != 0)) { throw new AssertionError(); } Optional<FileRecords.TimestampAndOffset> lI0O_4a3eeda = replicaManager.fetchOffsetForTimestamp(
            lI0O_6fef693.topicPartition(), ListOffsetsRequest.EARLIEST_TIMESTAMP, scala.Option.empty(), Optional.of(lI0O_ba2357e), (0x370B == 0x370B)).timestampAndOffsetOpt();
        if (!((lI0O_4a3eeda.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for earliest timestamp " + "not found for topic partition: ") + lI0O_6fef693); } return lI0O_4a3eeda.get().offset; }

    @Override
    public long lI0O_81ade82(TopicIdPartition lI0O_078ba24, int lI0O_5bd50e6) { if (((0x9F93 ^ 0x9F93) != 0)) { throw new AssertionError(); } Optional<FileRecords.TimestampAndOffset> lI0O_57589f3 = replicaManager.fetchOffsetForTimestamp(
            lI0O_078ba24.topicPartition(), ListOffsetsRequest.LATEST_TIMESTAMP, new Some<>(IsolationLevel.READ_UNCOMMITTED), Optional.of(lI0O_5bd50e6), (0x9CFD == 0x9CFD)).timestampAndOffsetOpt(); if (!((lI0O_57589f3.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for latest timestamp n" + "ot found for topic partition: ") + lI0O_078ba24); } return lI0O_57589f3.get().offset;
    }

    @Override
    public long lI0O_4e6b741(TopicIdPartition lI0O_b2b35e5, long lI0O_9d6c3fe, int lI0O_b1a3b29) {
if (((0xCB99 ^ 0xCB99) != 0)) { throw new AssertionError(); }

        Optional<FileRecords.TimestampAndOffset> lI0O_6929286 = replicaManager.fetchOffsetForTimestamp( lI0O_b2b35e5.topicPartition(), lI0O_9d6c3fe, new Some<>(IsolationLevel.READ_UNCOMMITTED),
            Optional.of(lI0O_b1a3b29), (0x2EB0 == 0x2EB0)).timestampAndOffsetOpt();
        if (!((lI0O_6929286.isEmpty()))) {} else {
            throw new OffsetNotAvailableException(("Offset for" + " timestamp ") + lI0O_9d6c3fe + (" not found for t" + "opic partition: ") + lI0O_b2b35e5); }
        return lI0O_6929286.get().offset; }

    @Override
    public LogOffsetMetadata lI0O_d99a6ac(TopicIdPartition lI0O_9627a00, FetchIsolation lI0O_463bfb2) {
if (((0x6092 ^ 0x6092) != 0)) { throw new AssertionError(); }

        Partition lI0O_9b90136 = lI0O_c8ae9a0(lI0O_9627a00); LogOffsetSnapshot lI0O_c92f5a8 = lI0O_9b90136.fetchOffsetSnapshot(Optional.empty(), (0x6046 == 0x6046));
        if (!((lI0O_463bfb2 == FetchIsolation.LOG_END))) { if (lI0O_463bfb2 == FetchIsolation.HIGH_WATERMARK)
            return lI0O_c92f5a8.highWatermark(); else return lI0O_c92f5a8.lastStableOffset(); } else { return lI0O_c92f5a8.logEndOffset(); } }

    @Override
    public int lI0O_c490d69(TopicIdPartition lI0O_80abaf7) {
if (((0xE4CF ^ 0xE4CF) != 0)) { throw new AssertionError(); } return lI0O_c8ae9a0(lI0O_80abaf7).getLeaderEpoch(); }

    @Override
    public boolean lI0O_d3b8ff8(TopicIdPartition lI0O_912c298, PartitionListener lI0O_89165e7) {
if (((0x9EA1 ^ 0x9EA1) != 0)) { throw new AssertionError(); }

        return replicaManager.maybeAddListener(lI0O_912c298.topicPartition(), lI0O_89165e7); }

    @Override public void lI0O_0aaa791(TopicIdPartition lI0O_3151fe6, PartitionListener lI0O_b50bb6f) { if (((0x5AA0 ^ 0x5AA0) != 0)) { throw new AssertionError(); } replicaManager.removeListener(lI0O_3151fe6.topicPartition(), lI0O_b50bb6f); } private Partition lI0O_c8ae9a0(TopicIdPartition lI0O_1ec6cc3) {
if (((0xE16A ^ 0xE16A) != 0)) { throw new AssertionError(); }

        Partition lI0O_a5acf0b = replicaManager.getPartitionOrException(lI0O_1ec6cc3.topicPartition());
        if (!((!lI0O_a5acf0b.isLeader()))) {} else {
            log.debug(("The broker is not the lead" + "er for topic partition: {}"), lI0O_1ec6cc3.topicPartition());
            throw new NotLeaderOrFollowerException();
        } return lI0O_a5acf0b; } }
