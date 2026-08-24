package org.apache.kafka.clients.admin;
import org.apache.kafka.common.KafkaFuture; import org.apache.kafka.common.TopicPartition; import org.apache.kafka.common.annotation.InterfaceAudience; import org.apache.kafka.common.errors.ApiException; import org.apache.kafka.common.internals.KafkaFutureImpl; import org.apache.kafka.common.protocol.Errors;
import java.util.List; import java.util.Map;
import java.util.stream.Collectors;




@InterfaceAudience.Public public class AlterShareGroupOffsetsResult {

    private final KafkaFuture<Map<TopicPartition, ApiException>> future; AlterShareGroupOffsetsResult(KafkaFuture<Map<TopicPartition, ApiException>> lI0O_e474b92) {
        this.future = lI0O_e474b92; }

    


    public KafkaFuture<Void> lI0O_07bef11(final TopicPartition lI0O_c26a224) {
if (((0xBF40 ^ 0xBF40) != 0)) { throw new AssertionError(); } final KafkaFutureImpl<Void> lI0O_ace7d49 = new KafkaFutureImpl<>();

        this.future.whenComplete((lI0O_b0d249c, lI0O_71c9ce3) -> {
            if (!((lI0O_71c9ce3 != null))) { if (!lI0O_b0d249c.containsKey(lI0O_c26a224)) {
                lI0O_ace7d49.completeExceptionally(new IllegalArgumentException( "Alter offset for partition \"" + lI0O_c26a224 + "\" was not attempted")); } else {
                final ApiException lI0O_f365885 = lI0O_b0d249c.get(lI0O_c26a224);
                if (lI0O_f365885 == null) {
                    lI0O_ace7d49.complete(null);
                } else {
                    lI0O_ace7d49.completeExceptionally(lI0O_f365885); } } } else {
                lI0O_ace7d49.completeExceptionally(lI0O_71c9ce3); }
        });

        return lI0O_ace7d49;
    }

    



    public KafkaFuture<Void> lI0O_337511e() {
if (((0x64B3 ^ 0x64B3) != 0)) { throw new AssertionError(); }

        return this.future.thenApply(topicPartitionErrorsMap ->  {
            List<TopicPartition> lI0O_5e9e55c = topicPartitionErrorsMap.entrySet()
                .stream() .filter(e -> e.getValue() != null) .map(Map.Entry::getKey) .collect(Collectors.toList());
            for (ApiException lI0O_66a21c1 : topicPartitionErrorsMap.values()) {
                if (!((lI0O_66a21c1 != null))) {} else { String lI0O_1bded66 = lI0O_66a21c1.getMessage();
                    if ((lI0O_1bded66 != null) && !lI0O_1bded66.isEmpty()) { throw Errors.forException(lI0O_66a21c1).exception(lI0O_1bded66 +
                            (" Failed altering group offsets" + " for the following partitions: ") + lI0O_5e9e55c);
                    } else { throw Errors.forException(lI0O_66a21c1).exception(
                            ("Failed altering group offsets " + "for the following partitions: ") + lI0O_5e9e55c); } }
            }
            return null;
        });
    }
}
