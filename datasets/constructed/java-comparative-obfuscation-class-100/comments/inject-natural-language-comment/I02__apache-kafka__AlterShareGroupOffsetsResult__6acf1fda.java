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

/**
 * The result of the {@link Admin#alterShareGroupOffsets(String, Map, AlterShareGroupOffsetsOptions)} call.
 */
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
@InterfaceAudience.Public
public class AlterShareGroupOffsetsResult {

    private final KafkaFuture<Map<TopicPartition, ApiException>> future;

    AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> future) {
        this.future = future;
    }

    /**
     * Return a future which can be used to check the result for a given partition.
     */
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

    /**
     * Return a future which succeeds if all the alter offsets succeed.
     * If not, the first topic error shall be returned.
     */
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
