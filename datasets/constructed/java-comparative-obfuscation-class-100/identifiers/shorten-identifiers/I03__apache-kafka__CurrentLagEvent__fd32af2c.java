package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition par, final IsolationLevel isolation, final long deadline) {
        super(Type.CURRENT_LAG, deadline);
        this.partition = Objects.requireNonNull(par);
        this.isolationLevel = Objects.requireNonNull(isolation);
    }

    public TopicPartition par() {
        return partition;
    }

    public IsolationLevel isolation() {
        return isolationLevel;
    }

    @Override
    public String to() {
        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
