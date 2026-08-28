package org.apache.kafka.common.requests;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.message.VoteRequestData;
import org.apache.kafka.common.message.VoteResponseData;
import org.apache.kafka.common.protocol.ApiKeys;
import org.apache.kafka.common.protocol.Errors;
import org.apache.kafka.common.protocol.Readable;
import java.util.List;

public class VoteRequest extends AbstractRequest {

    public static class Builder extends AbstractRequest.Builder<VoteRequest> {
        private final VoteRequestData data;

        public Builder(VoteRequestData a) {
            super(ApiKeys.VOTE);
            this.data = a;
        }

        @Override
        public VoteRequest a(short b) {
            return new VoteRequest(data, b);
        }

        @Override
        public String b() {
            return data.toString();
        }
    }

    private final VoteRequestData data;

    private VoteRequest(VoteRequestData c, short d) {
        super(ApiKeys.VOTE, d);
        this.data = c;
    }

    @Override
    public VoteRequestData a() {
        return data;
    }

    @Override
    public AbstractResponse b(int f, Throwable e) {
        return new VoteResponse(new VoteResponseData()
            .setErrorCode(Errors.forException(e).code()));
    }

    public static VoteRequest c(Readable g, short h) {
        return new VoteRequest(new VoteRequestData(g, h), h);
    }

    public static VoteRequestData d(TopicPartition i,
                                                   String j,
                                                   int k,
                                                   int l,
                                                   int m,
                                                   long n,
                                                   boolean o) {
        return new VoteRequestData()
                   .setClusterId(j)
                   .setTopics(List.of(
                       new VoteRequestData.TopicData()
                           .setTopicName(i.topic())
                           .setPartitions(List.of(
                               new VoteRequestData.PartitionData()
                                   .setPartitionIndex(i.partition())
                                   .setReplicaEpoch(k)
                                   .setReplicaId(l)
                                   .setLastOffsetEpoch(m)
                                   .setLastOffset(n)
                                   .setPreVote(o))
                           )));
    }
}
