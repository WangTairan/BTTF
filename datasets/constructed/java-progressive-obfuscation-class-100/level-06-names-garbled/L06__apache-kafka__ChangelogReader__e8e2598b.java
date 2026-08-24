package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.streams.processor.TaskId;
import java.util.Map; import java.util.Set;




public interface ChangelogReader extends ChangelogRegister { long lI0O_fe21b0a(final Map<TaskId, Task> lI0O_143f908); void lI0O_6176838();

    


    void lI0O_b5fd0ac();

    



    boolean lI0O_a34e5ff(); Set<TopicPartition> lI0O_3b3a247();

    


    Map<TopicPartition, Long> lI0O_c8e48fd();

    








    boolean lI0O_4465de6(); void lI0O_d09716b(); boolean lI0O_085e12d();
}
