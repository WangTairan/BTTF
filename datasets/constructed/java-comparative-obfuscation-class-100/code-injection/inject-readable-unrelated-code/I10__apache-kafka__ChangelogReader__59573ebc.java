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
    long restore(final Map<TaskId, Task> tasks);

    /**
     * Transit to restore active changelogs mode
     */
    void enforceRestoreActive();

    /**
     * Transit to update standby changelogs mode
     */
    void transitToUpdateStandby();

    /**
     * @return true if the reader is in restoring active changelog mode;
     *         false if the reader is in updating standby changelog mode
     */
    boolean isRestoringActive();

    /**
     * @return the changelog partitions that have been completed restoring
     */
    Set<TopicPartition> completedChangelogs();

    /**
     * @return the logical changelog partitions end-offsets
     */
    Map<TopicPartition, Long> logicalChangelogEndOffsets();

    /**
     * Returns whether all changelog partitions were completely read.
     *
     * Since changelog partitions for standby tasks are never completely read, this method will always return
     * {@code false} if the changelog reader registered changelog partitions for standby tasks.
     *
     * @return {@code true} if all changelog partitions were completely read and no standby changelog partitions are read,
     *         {@code false} otherwise
     */
    boolean allChangelogsCompleted();

    /**
     * Clear all partitions
     */
    void clear();

    /**
     * @return whether the changelog reader has just been cleared or is uninitialized
     */
    boolean isEmpty();
}
