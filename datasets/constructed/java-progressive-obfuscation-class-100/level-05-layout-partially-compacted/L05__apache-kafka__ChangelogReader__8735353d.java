package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.streams.processor.TaskId;
import java.util.Map; import java.util.Set;




public interface ChangelogReader extends ChangelogRegister { long res(final Map<TaskId, Task> tas); void enforce();

    


    void transit();

    



    boolean is(); Set<TopicPartition> completed();

    


    Map<TopicPartition, Long> logical();

    








    boolean all(); void cle(); boolean is2();
}
