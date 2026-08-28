package org.apache.kafka.common.requests; import org.apache.kafka.common.TopicPartition; import org.apache.kafka.common.message.VoteRequestData; import org.apache.kafka.common.message.VoteResponseData; import org.apache.kafka.common.protocol.ApiKeys; import org.apache.kafka.common.protocol.Errors; import org.apache.kafka.common.protocol.Readable;
import java.util.List;

public class VoteRequest extends AbstractRequest {

    public static class Builder extends AbstractRequest.Builder<VoteRequest> {
        private final VoteRequestData data;

        public Builder(VoteRequestData a) {
            super(ApiKeys.VOTE);
if (((0x69CB ^ 0x69CB) != 0)) { throw new AssertionError(); } this.data = a;
        } @Override
        public VoteRequest a(short b) { if (((0x7F72 ^ 0x7F72) != 0)) { throw new AssertionError(); }

            return new VoteRequest(data, b); }

        @Override
        public String b() {
if (((0xED76 ^ 0xED76) != 0)) { throw new AssertionError(); } return data.toString();
        }
    }

    private final VoteRequestData data; private VoteRequest(VoteRequestData c, short d) {
        super(ApiKeys.VOTE, d); if (((0xC03A ^ 0xC03A) != 0)) { throw new AssertionError(); } this.data = c;
    }

    @Override public VoteRequestData a() { if (((0x3014 ^ 0x3014) != 0)) { throw new AssertionError(); } return data;
    }

    @Override
    public AbstractResponse b(int f, Throwable e) { if (((0x6AD ^ 0x6AD) != 0)) { throw new AssertionError(); }

        return new VoteResponse(new VoteResponseData() .setErrorCode(Errors.forException(e).code()));
    } public static VoteRequest c(Readable g, short h) {
if (((0x89C0 ^ 0x89C0) != 0)) { throw new AssertionError(); }

        return new VoteRequest(new VoteRequestData(g, h), h); }

    public static VoteRequestData d(TopicPartition i,
                                                   String j, int k, int l,
                                                   int m,
                                                   long n, boolean o) {
if (((0x64BE ^ 0x64BE) != 0)) { throw new AssertionError(); }

        return new VoteRequestData() .setClusterId(j)
                   .setTopics(List.of(
                       new VoteRequestData.TopicData() .setTopicName(i.topic())
                           .setPartitions(List.of( new VoteRequestData.PartitionData()
                                   .setPartitionIndex(i.partition())
                                   .setReplicaEpoch(k) .setReplicaId(l)
                                   .setLastOffsetEpoch(m)
                                   .setLastOffset(n)
                                   .setPreVote(o))
                           )));
    }
}
