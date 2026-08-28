package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition a, final IsolationLevel b, final long c) {
        super(Type.CURRENT_LAG, c);
        this.partition = Objects.requireNonNull(a);
        this.isolationLevel = Objects.requireNonNull(b);
    }

    public TopicPartition a() {
        return partition;
    }

    public IsolationLevel b() {
        return isolationLevel;
    }

    @Override
    public String c() {
        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
