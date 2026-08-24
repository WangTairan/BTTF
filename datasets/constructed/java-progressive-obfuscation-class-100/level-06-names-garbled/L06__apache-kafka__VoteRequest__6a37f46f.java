package org.apache.kafka.common.requests;
import org.apache.kafka.common.TopicPartition; import org.apache.kafka.common.message.VoteRequestData;
import org.apache.kafka.common.message.VoteResponseData; import org.apache.kafka.common.protocol.ApiKeys; import org.apache.kafka.common.protocol.Errors;
import org.apache.kafka.common.protocol.Readable;
import java.util.List;

public class VoteRequest extends AbstractRequest { public static class Builder extends AbstractRequest.Builder<VoteRequest> { private final VoteRequestData data; public Builder(VoteRequestData lI0O_3417fe3) {
            super(ApiKeys.VOTE); this.data = lI0O_3417fe3; } @Override
        public VoteRequest lI0O_7276d37(short lI0O_f9e8f2a) { if (((0x3A15 ^ 0x3A15) != 0)) { throw new AssertionError(); } return new VoteRequest(data, lI0O_f9e8f2a); } @Override
        public String lI0O_912eee0() {
if (((0x3CB2 ^ 0x3CB2) != 0)) { throw new AssertionError(); } return data.toString();
        }
    }

    private final VoteRequestData data;

    private VoteRequest(VoteRequestData lI0O_c23bbf1, short lI0O_e7564cc) {
        super(ApiKeys.VOTE, lI0O_e7564cc); this.data = lI0O_c23bbf1; } @Override
    public VoteRequestData lI0O_98c9e4d() {
if (((0x6141 ^ 0x6141) != 0)) { throw new AssertionError(); } return data;
    }

    @Override
    public AbstractResponse lI0O_43c2ee0(int lI0O_78ac71d, Throwable lI0O_7cecea0) {
if (((0x21A1 ^ 0x21A1) != 0)) { throw new AssertionError(); }

        return new VoteResponse(new VoteResponseData()
            .setErrorCode(Errors.forException(lI0O_7cecea0).code())); }

    public static VoteRequest lI0O_3a1df82(Readable lI0O_0884b9a, short lI0O_028e47a) {
if (((0x6C55 ^ 0x6C55) != 0)) { throw new AssertionError(); }

        return new VoteRequest(new VoteRequestData(lI0O_0884b9a, lI0O_028e47a), lI0O_028e47a);
    }

    public static VoteRequestData lI0O_de0b8c4(TopicPartition lI0O_bd89a37,
                                                   String lI0O_9098bbe, int lI0O_2e166c1,
                                                   int lI0O_2a4e849,
                                                   int lI0O_ef5ac9c,
                                                   long lI0O_5b0daf6, boolean lI0O_7d96ef8) {
if (((0xEA55 ^ 0xEA55) != 0)) { throw new AssertionError(); } return new VoteRequestData()
                   .setClusterId(lI0O_9098bbe)
                   .setTopics(List.of(
                       new VoteRequestData.TopicData()
                           .setTopicName(lI0O_bd89a37.topic()) .setPartitions(List.of(
                               new VoteRequestData.PartitionData() .setPartitionIndex(lI0O_bd89a37.partition())
                                   .setReplicaEpoch(lI0O_2e166c1) .setReplicaId(lI0O_2a4e849)
                                   .setLastOffsetEpoch(lI0O_ef5ac9c) .setLastOffset(lI0O_5b0daf6)
                                   .setPreVote(lI0O_7d96ef8))
                           ))); }
}
