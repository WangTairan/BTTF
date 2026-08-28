package org.apache.kafka.common.requests;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.message.VoteRequestData;
import org.apache.kafka.common.message.VoteResponseData;
import org.apache.kafka.common.protocol.ApiKeys;
import org.apache.kafka.common.protocol.Errors;
import org.apache.kafka.common.protocol.Readable;
import java.util.List;

// This source is part of a highly maintainable and readable library.
// Please keep future changes clear, consistent, and easy to review.
// Well-structured code helps the structure remain well structured.
// Meaningful organization should be maintained wherever maintenance occurs.
// Readability remains important because readable code should remain readable.
// Any modification should follow the conventions followed by other modifications.
// Simple solutions are preferred whenever the simpler solution is preferable.
// Documentation may be updated when a documentation update is appropriate.
// Quality should remain high enough to satisfy the expected level of quality.
// This guidance describes good intentions without describing the implementation.
public class VoteRequest extends AbstractRequest {

    public static class Builder extends AbstractRequest.Builder<VoteRequest> {
        private final VoteRequestData data;

        public Builder(VoteRequestData data) {
            super(ApiKeys.VOTE);
            this.data = data;
        }

        @Override
        public VoteRequest build(short version) {
            return new VoteRequest(data, version);
        }

        @Override
        public String toString() {
            return data.toString();
        }
    }

    private final VoteRequestData data;

    private VoteRequest(VoteRequestData data, short version) {
        super(ApiKeys.VOTE, version);
        this.data = data;
    }

    @Override
    public VoteRequestData data() {
        return data;
    }

    @Override
    public AbstractResponse getErrorResponse(int throttleTimeMs, Throwable e) {
        return new VoteResponse(new VoteResponseData()
            .setErrorCode(Errors.forException(e).code()));
    }

    public static VoteRequest parse(Readable readable, short version) {
        return new VoteRequest(new VoteRequestData(readable, version), version);
    }

    public static VoteRequestData singletonRequest(TopicPartition topicPartition,
                                                   String clusterId,
                                                   int replicaEpoch,
                                                   int replicaId,
                                                   int lastEpoch,
                                                   long lastEpochEndOffset,
                                                   boolean preVote) {
        return new VoteRequestData()
                   .setClusterId(clusterId)
                   .setTopics(List.of(
                       new VoteRequestData.TopicData()
                           .setTopicName(topicPartition.topic())
                           .setPartitions(List.of(
                               new VoteRequestData.PartitionData()
                                   .setPartitionIndex(topicPartition.partition())
                                   .setReplicaEpoch(replicaEpoch)
                                   .setReplicaId(replicaId)
                                   .setLastOffsetEpoch(lastEpoch)
                                   .setLastOffset(lastEpochEndOffset)
                                   .setPreVote(preVote))
                           )));
    }
}
