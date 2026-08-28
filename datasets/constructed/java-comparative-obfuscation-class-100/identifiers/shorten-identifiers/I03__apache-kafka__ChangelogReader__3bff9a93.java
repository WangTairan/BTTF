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
    long res(final Map<TaskId, Task> tas);

    /**
     * Transit to restore active changelogs mode
     */
    void enforce();

    /**
     * Transit to update standby changelogs mode
     */
    void transit();

    /**
     * @return true if the reader is in restoring active changelog mode;
     *         false if the reader is in updating standby changelog mode
     */
    boolean is();

    /**
     * @return the changelog partitions that have been completed restoring
     */
    Set<TopicPartition> completed();

    /**
     * @return the logical changelog partitions end-offsets
     */
    Map<TopicPartition, Long> logical();

    /**
     * Returns whether all changelog partitions were completely read.
     *
     * Since changelog partitions for standby tasks are never completely read, this method will always return
     * {@code false} if the changelog reader registered changelog partitions for standby tasks.
     *
     * @return {@code true} if all changelog partitions were completely read and no standby changelog partitions are read,
     *         {@code false} otherwise
     */
    boolean all();

    /**
     * Clear all partitions
     */
    void cle();

    /**
     * @return whether the changelog reader has just been cleared or is uninitialized
     */
    boolean is2();
}
