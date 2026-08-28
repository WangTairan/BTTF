package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.streams.processor.TaskId;
import java.util.Map; import java.util.Set;




public interface ChangelogReader extends ChangelogRegister { long a(final Map<TaskId, Task> a);

    


    void b(); void c();

    



    boolean d();

    


    Set<TopicPartition> e(); Map<TopicPartition, Long> f();

    








    boolean g(); void h();

    


    boolean i(); }
