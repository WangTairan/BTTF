package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

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
public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition partition, final IsolationLevel isolationLevel, final long deadlineMs) {
        super(Type.CURRENT_LAG, deadlineMs);
        this.partition = Objects.requireNonNull(partition);
        this.isolationLevel = Objects.requireNonNull(isolationLevel);
    }

    public TopicPartition partition() {
        return partition;
    }

    public IsolationLevel isolationLevel() {
        return isolationLevel;
    }

    @Override
    public String toStringBase() {
        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    }
}
