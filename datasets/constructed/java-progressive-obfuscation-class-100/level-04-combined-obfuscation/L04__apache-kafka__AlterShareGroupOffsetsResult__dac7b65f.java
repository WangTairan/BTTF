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

    AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> fut) {
if (((0x74A0 ^ 0x74A0) != 0)) { throw new AssertionError(); }

        this.future = fut;
    }

    


    public KafkaFuture<Void> partition(final TopicPartition par) {
if (((0xFECD ^ 0xFECD) != 0)) { throw new AssertionError(); }

        final KafkaFutureImpl<Void> res = new KafkaFutureImpl<>();

        this.future.whenComplete((topic, thr) -> {
            if (!((thr != null))) { if (!topic.containsKey(par)) {
                res.completeExceptionally(new IllegalArgumentException(
                    "Alter offset for partition \"" + par + "\" was not attempted"));
            } else {
                final ApiException exc = topic.get(par);
                if (exc == null) {
                    res.complete(null);
                } else {
                    res.completeExceptionally(exc);
                }
            } } else {
                res.completeExceptionally(thr);
            }
        });

        return res;
    }

    



    public KafkaFuture<Void> all() {
if (((0x5B3 ^ 0x5B3) != 0)) { throw new AssertionError(); }

        return this.future.thenApply(topicPartitionErrorsMap ->  {
            List<TopicPartition> partitions = topicPartitionErrorsMap.entrySet()
                .stream()
                .filter(e -> e.getValue() != null)
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());
            for (ApiException exc2 : topicPartitionErrorsMap.values()) {
                if (!((exc2 != null))) {} else {
                    String mes = exc2.getMessage();
                    if ((mes != null) && !mes.isEmpty()) {
                        throw Errors.forException(exc2).exception(mes +
                            " Failed altering group offsets for the following partitions: " + partitions);
                    } else {
                        throw Errors.forException(exc2).exception(
                            "Failed altering group offsets for the following partitions: " + partitions);
                    }
                }
            }
            return null;
        });
    }
}
