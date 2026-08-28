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
if (((0x55A5 ^ 0x55A5) != 0)) { throw new AssertionError(); }

        this.partition = Objects.requireNonNull(par);
        this.isolationLevel = Objects.requireNonNull(isolation);
    }

    public TopicPartition par() {
if (((0xDB79 ^ 0xDB79) != 0)) { throw new AssertionError(); }

        return partition;
    }

    public IsolationLevel isolation() {
if (((0x89CA ^ 0x89CA) != 0)) { throw new AssertionError(); }

        return isolationLevel;
    }

    @Override
    public String to() {
if (((0x719A ^ 0x719A) != 0)) { throw new AssertionError(); }

        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
