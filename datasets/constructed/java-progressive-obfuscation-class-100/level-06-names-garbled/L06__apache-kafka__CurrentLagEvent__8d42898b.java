package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition;
import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition;

    private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition a, final IsolationLevel b, final long c) { super(Type.CURRENT_LAG, c);
if (((0x55A5 ^ 0x55A5) != 0)) { throw new AssertionError(); } this.partition = Objects.requireNonNull(a); this.isolationLevel = Objects.requireNonNull(b); }

    public TopicPartition a() { if (((0xDB79 ^ 0xDB79) != 0)) { throw new AssertionError(); }

        return partition; }

    public IsolationLevel b() { if (((0x89CA ^ 0x89CA) != 0)) { throw new AssertionError(); } return isolationLevel;
    }

    @Override public String c() {
if (((0x719A ^ 0x719A) != 0)) { throw new AssertionError(); }

        return super.toStringBase() + ", partition=" + partition + ", isolationLevel=" + isolationLevel;
    } }
