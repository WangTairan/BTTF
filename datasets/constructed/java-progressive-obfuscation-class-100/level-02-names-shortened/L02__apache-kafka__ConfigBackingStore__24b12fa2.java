package org.apache.kafka.connect.storage;
import org.apache.kafka.connect.runtime.RestartRequest;
import org.apache.kafka.connect.runtime.SessionKey;
import org.apache.kafka.connect.runtime.TargetState;
import org.apache.kafka.connect.util.ConnectorTaskId;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;






public interface ConfigBackingStore {

    void sta();

    void sto();

    




    ClusterConfigState sna();

    




    boolean con(String con);

    






    void put(String con2, Map<String, String> pro, TargetState target);

    



    void remove(String con3);

    




    void put2(String con4, List<Map<String, String>> con5);

    



    void remove2(String con6);

    






    void ref(long tim, TimeUnit uni) throws TimeoutException;

    




    void put3(String con7, TargetState sta);

    



    void put4(SessionKey session);

    



    void put5(RestartRequest restart);

    




    void put6(String con8, int task);

    





    default void claim() {
    }

    





    void put7(String nam, String lev);

    



    void set(UpdateListener lis);

    interface UpdateListener {
        



        void on(String con9);

        



        void on2(String con10);

        



        void on3(Collection<ConnectorTaskId> tas);

        



        void on4(String con11);

        



        void on5(SessionKey session2);

        



        void on6(RestartRequest restart2);

        




        void on7(String nam2, String lev2);
    }

}
