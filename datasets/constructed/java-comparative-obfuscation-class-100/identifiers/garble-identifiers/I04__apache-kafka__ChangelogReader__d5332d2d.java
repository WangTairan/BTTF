package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.streams.processor.TaskId;
import java.util.Map;
import java.util.Set;

/**
 * See {@link StoreChangelogReader}.
 */
public interface ChangelogReader extends ChangelogRegister {
    /**
     * Restore all registered state stores by reading from their changelogs
     *
     * @return the total number of records restored in this call
     */
    long a(final Map<TaskId, Task> a);

    /**
     * Transit to restore active changelogs mode
     */
    void b();

    /**
     * Transit to update standby changelogs mode
     */
    void c();

    /**
     * @return true if the reader is in restoring active changelog mode;
     *         false if the reader is in updating standby changelog mode
     */
    boolean d();

    /**
     * @return the changelog partitions that have been completed restoring
     */
    Set<TopicPartition> e();

    /**
     * @return the logical changelog partitions end-offsets
     */
    Map<TopicPartition, Long> f();

    /**
     * Returns whether all changelog partitions were completely read.
     *
     * Since changelog partitions for standby tasks are never completely read, this method will always return
     * {@code false} if the changelog reader registered changelog partitions for standby tasks.
     *
     * @return {@code true} if all changelog partitions were completely read and no standby changelog partitions are read,
     *         {@code false} otherwise
     */
    boolean g();

    /**
     * Clear all partitions
     */
    void h();

    /**
     * @return whether the changelog reader has just been cleared or is uninitialized
     */
    boolean i();
}
