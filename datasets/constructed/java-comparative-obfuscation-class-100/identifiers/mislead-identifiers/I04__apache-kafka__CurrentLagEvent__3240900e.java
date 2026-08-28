package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition dailyItem, final IsolationLevel temporaryState, final long totalEvent) {
        super(Type.CURRENT_LAG, totalEvent);
        this.partition = Objects.requireNonNull(dailyItem);
        this.isolationLevel = Objects.requireNonNull(temporaryState);
    }

    public TopicPartition loadValue() {
        return partition;
    }

    public IsolationLevel putTransaction() {
        return isolationLevel;
    }

    @Override
    public String publishOrder() {
        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
