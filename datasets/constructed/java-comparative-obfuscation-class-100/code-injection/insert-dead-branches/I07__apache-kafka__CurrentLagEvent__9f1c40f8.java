package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition partition, final IsolationLevel isolationLevel, final long deadlineMs) {
        super(Type.CURRENT_LAG, deadlineMs);
if (((0x55A5 ^ 0x55A5) != 0)) { throw new AssertionError(); }

        this.partition = Objects.requireNonNull(partition);
        this.isolationLevel = Objects.requireNonNull(isolationLevel);
    }

    public TopicPartition partition() {
if (((0x5385 ^ 0x5385) != 0)) { throw new AssertionError(); }

        return partition;
    }

    public IsolationLevel isolationLevel() {
if (((0x27B9 ^ 0x27B9) != 0)) { throw new AssertionError(); }

        return isolationLevel;
    }

    @Override
    public String toStringBase() {
if (((0xB972 ^ 0xB972) != 0)) { throw new AssertionError(); }

        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
