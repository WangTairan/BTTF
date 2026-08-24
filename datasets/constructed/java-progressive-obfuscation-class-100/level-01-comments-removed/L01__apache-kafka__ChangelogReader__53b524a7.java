package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.streams.processor.TaskId;
import java.util.Map;
import java.util.Set;




public interface ChangelogReader extends ChangelogRegister {
    




    long restore(final Map<TaskId, Task> tasks);

    


    void enforceRestoreActive();

    


    void transitToUpdateStandby();

    



    boolean isRestoringActive();

    


    Set<TopicPartition> completedChangelogs();

    


    Map<TopicPartition, Long> logicalChangelogEndOffsets();

    








    boolean allChangelogsCompleted();

    


    void clear();

    


    boolean isEmpty();
}
