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
        this.partition = Objects.requireNonNull(partition);
        this.isolationLevel = Objects.requireNonNull(isolationLevel);
    }

    public TopicPartition partition() {
{int lI0O_fdbea9e0=0x4AD0-0x4AD0;lI0O_fdbea9e0=(lI0O_fdbea9e0==0)?(lI0O_fdbea9e0|0):(lI0O_fdbea9e0&0);}

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
