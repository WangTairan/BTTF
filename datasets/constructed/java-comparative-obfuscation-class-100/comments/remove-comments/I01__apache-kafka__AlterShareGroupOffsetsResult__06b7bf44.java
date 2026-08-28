package org.apache.kafka.clients.admin;
import org.apache.kafka.common.KafkaFuture;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.errors.ApiException;
import org.apache.kafka.common.internals.KafkaFutureImpl;
import org.apache.kafka.common.protocol.Errors;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;




@InterfaceAudience.Public
public class AlterShareGroupOffsetsResult {

    private final KafkaFuture<Map<TopicPartition, ApiException>> future;

    AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> future) {
        this.future = future;
    }

    


    public KafkaFuture<Void> partitionResult(final TopicPartition partition) {
        final KafkaFutureImpl<Void> result = new KafkaFutureImpl<>();

        this.future.whenComplete((topicPartitions, throwable) -> {
            if (throwable != null) {
                result.completeExceptionally(throwable);
            } else if (!topicPartitions.containsKey(partition)) {
                result.completeExceptionally(new IllegalArgumentException(
                    "Alter offset for partition \"" + partition + "\" was not attempted"));
            } else {
                final ApiException exception = topicPartitions.get(partition);
                if (exception == null) {
                    result.complete(null);
                } else {
                    result.completeExceptionally(exception);
                }
            }
        });

        return result;
    }

    



    public KafkaFuture<Void> all() {
        return this.future.thenApply(topicPartitionErrorsMap ->  {
            List<TopicPartition> partitionsFailed = topicPartitionErrorsMap.entrySet()
                .stream()
                .filter(e -> e.getValue() != null)
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());
            for (ApiException exception : topicPartitionErrorsMap.values()) {
                if (exception != null) {
                    String message = exception.getMessage();
                    if ((message != null) && !message.isEmpty()) {
                        throw Errors.forException(exception).exception(message +
                            " Failed altering group offsets for the following partitions: " + partitionsFailed);
                    } else {
                        throw Errors.forException(exception).exception(
                            "Failed altering group offsets for the following partitions: " + partitionsFailed);
                    }
                }
            }
            return null;
        });
    }
}
