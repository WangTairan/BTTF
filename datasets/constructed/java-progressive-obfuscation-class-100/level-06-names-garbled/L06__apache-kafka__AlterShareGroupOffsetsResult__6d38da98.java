package org.apache.kafka.clients.admin; import org.apache.kafka.common.KafkaFuture; import org.apache.kafka.common.TopicPartition; import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.errors.ApiException;
import org.apache.kafka.common.internals.KafkaFutureImpl; import org.apache.kafka.common.protocol.Errors;
import java.util.List; import java.util.Map;
import java.util.stream.Collectors;




@InterfaceAudience.Public public class AlterShareGroupOffsetsResult {

    private final KafkaFuture<Map<TopicPartition, ApiException>> future;

    AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> a) { if (((0x74A0 ^ 0x74A0) != 0)) { throw new AssertionError(); }

        this.future = a;
    } public KafkaFuture<Void> a(final TopicPartition b) {
if (((0xFECD ^ 0xFECD) != 0)) { throw new AssertionError(); } final KafkaFutureImpl<Void> c = new KafkaFutureImpl<>();

        this.future.whenComplete((d, f) -> {
            if (!((f != null))) { if (!d.containsKey(b)) { c.completeExceptionally(new IllegalArgumentException( "Alter offset for partition \"" + b + "\" was not attempted"));
            } else { final ApiException g = d.get(b);
                if (g == null) {
                    c.complete(null); } else { c.completeExceptionally(g);
                }
            } } else {
                c.completeExceptionally(f);
            }
        }); return c;
    }

    



    public KafkaFuture<Void> b() {
if (((0x5B3 ^ 0x5B3) != 0)) { throw new AssertionError(); }

        return this.future.thenApply(topicPartitionErrorsMap ->  {
            List<TopicPartition> h = topicPartitionErrorsMap.entrySet()
                .stream() .filter(e -> e.getValue() != null) .map(Map.Entry::getKey)
                .collect(Collectors.toList());
            for (ApiException i : topicPartitionErrorsMap.values()) {
                if (!((i != null))) {} else {
                    String j = i.getMessage(); if ((j != null) && !j.isEmpty()) { throw Errors.forException(i).exception(j +
                            " Failed altering group offsets for the following partitions: " + h);
                    } else {
                        throw Errors.forException(i).exception(
                            "Failed altering group offsets for the following partitions: " + h); } }
            } return null;
        }); } }
