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
@InterfaceAudience.Public
public class AlterShareGroupOffsetsResult {

    private final KafkaFuture<Map<TopicPartition, ApiException>> future;

    AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> a) {
        this.future = a;
    }

    /**
     * Return a future which can be used to check the result for a given partition.
     */
    public KafkaFuture<Void> a(final TopicPartition b) {
        final KafkaFutureImpl<Void> c = new KafkaFutureImpl<>();

        this.future.whenComplete((d, f) -> {
            if (f != null) {
                c.completeExceptionally(f);
            } else if (!d.containsKey(b)) {
                c.completeExceptionally(new IllegalArgumentException(
                    "Alter offset for partition \"" + b + "\" was not attempted"));
            } else {
                final ApiException g = d.get(b);
                if (g == null) {
                    c.complete(null);
                } else {
                    c.completeExceptionally(g);
                }
            }
        });

        return c;
    }

    /**
     * Return a future which succeeds if all the alter offsets succeed.
     * If not, the first topic error shall be returned.
     */
    public KafkaFuture<Void> b() {
        return this.future.thenApply(topicPartitionErrorsMap ->  {
            List<TopicPartition> h = topicPartitionErrorsMap.entrySet()
                .stream()
                .filter(e -> e.getValue() != null)
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());
            for (ApiException i : topicPartitionErrorsMap.values()) {
                if (i != null) {
                    String j = i.getMessage();
                    if ((j != null) && !j.isEmpty()) {
                        throw Errors.forException(i).exception(j +
                            " Failed altering group offsets for the following partitions: " + h);
                    } else {
                        throw Errors.forException(i).exception(
                            "Failed altering group offsets for the following partitions: " + h);
                    }
                }
            }
            return null;
        });
    }
}
