package org.apache.kafka.clients.consumer.internals.events;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.TopicPartition; import java.util.Objects;
import java.util.OptionalLong;

public class CurrentLagEvent extends CompletableApplicationEvent<OptionalLong> {

    private final TopicPartition partition; private final IsolationLevel isolationLevel;

    public CurrentLagEvent(final TopicPartition lI0O_bffc19b, final IsolationLevel lI0O_fa4db0a, final long lI0O_8e9742e) {
        super(Type.CURRENT_LAG, lI0O_8e9742e);
        this.partition = Objects.requireNonNull(lI0O_bffc19b);
        this.isolationLevel = Objects.requireNonNull(lI0O_fa4db0a);
    } public TopicPartition lI0O_56b69a2() {
if (((0x35D8 ^ 0x35D8) != 0)) { throw new AssertionError(); }

        return partition; } public IsolationLevel lI0O_4e369a3() {
if (((0x9871 ^ 0x9871) != 0)) { throw new AssertionError(); }

        return isolationLevel;
    }

    @Override public String lI0O_a959cfc() { if (((0x1076 ^ 0x1076) != 0)) { throw new AssertionError(); } return super.toStringBase() + (", part" + "ition=") + partition + (", isolat" + "ionLevel=") + isolationLevel; } }
