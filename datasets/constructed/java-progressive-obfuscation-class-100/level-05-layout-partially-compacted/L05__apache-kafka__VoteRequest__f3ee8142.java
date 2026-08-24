package org.apache.kafka.common.requests;
import org.apache.kafka.common.TopicPartition; import org.apache.kafka.common.message.VoteRequestData;
import org.apache.kafka.common.message.VoteResponseData; import org.apache.kafka.common.protocol.ApiKeys; import org.apache.kafka.common.protocol.Errors;
import org.apache.kafka.common.protocol.Readable;
import java.util.List;

public class VoteRequest extends AbstractRequest { public static class Builder extends AbstractRequest.Builder<VoteRequest> { private final VoteRequestData data; public Builder(VoteRequestData dat) {
            super(ApiKeys.VOTE); this.data = dat; } @Override
        public VoteRequest bui(short ver) { if (((0x3A15 ^ 0x3A15) != 0)) { throw new AssertionError(); } return new VoteRequest(data, ver); } @Override
        public String to() {
if (((0x3CB2 ^ 0x3CB2) != 0)) { throw new AssertionError(); } return data.toString();
        }
    }

    private final VoteRequestData data;

    private VoteRequest(VoteRequestData dat2, short ver2) {
        super(ApiKeys.VOTE, ver2); this.data = dat2; } @Override
    public VoteRequestData dat() {
if (((0x6141 ^ 0x6141) != 0)) { throw new AssertionError(); } return data;
    }

    @Override
    public AbstractResponse get(int throttle, Throwable e) {
if (((0x21A1 ^ 0x21A1) != 0)) { throw new AssertionError(); }

        return new VoteResponse(new VoteResponseData()
            .setErrorCode(Errors.forException(e).code())); }

    public static VoteRequest par(Readable rea, short ver3) {
if (((0x6C55 ^ 0x6C55) != 0)) { throw new AssertionError(); }

        return new VoteRequest(new VoteRequestData(rea, ver3), ver3);
    }

    public static VoteRequestData singleton(TopicPartition topic2,
                                                   String cluster, int replica,
                                                   int replica2,
                                                   int last,
                                                   long last2, boolean pre) {
if (((0xEA55 ^ 0xEA55) != 0)) { throw new AssertionError(); } return new VoteRequestData()
                   .setClusterId(cluster)
                   .setTopics(List.of(
                       new VoteRequestData.TopicData()
                           .setTopicName(topic2.topic()) .setPartitions(List.of(
                               new VoteRequestData.PartitionData() .setPartitionIndex(topic2.partition())
                                   .setReplicaEpoch(replica) .setReplicaId(replica2)
                                   .setLastOffsetEpoch(last) .setLastOffset(last2)
                                   .setPreVote(pre))
                           ))); }
}
