package org.apache.kafka.connect.storage;
import org.apache.kafka.connect.runtime.RestartRequest;
import org.apache.kafka.connect.runtime.SessionKey;
import org.apache.kafka.connect.runtime.TargetState; import org.apache.kafka.connect.util.ConnectorTaskId; import java.util.Collection;
import java.util.List;
import java.util.Map; import java.util.concurrent.TimeUnit; import java.util.concurrent.TimeoutException;






public interface ConfigBackingStore {

    void lI0O_c1294f1(); void lI0O_9d60670(); ClusterConfigState lI0O_b9b5b75(); boolean lI0O_0b423c9(String lI0O_ce067f4);

    






    void lI0O_3233b76(String lI0O_304e4a5, Map<String, String> lI0O_82acce2, TargetState lI0O_c38a0f9); void lI0O_b4b4bf4(String lI0O_a7d43d3); void lI0O_d540d79(String lI0O_4b930eb, List<Map<String, String>> lI0O_b71b335);

    



    void lI0O_732549e(String lI0O_4d7679b); void lI0O_8ddb54b(long lI0O_b4a4afa, TimeUnit lI0O_d916b2d) throws TimeoutException;

    




    void lI0O_cca426f(String lI0O_82ba268, TargetState lI0O_209ac87); void lI0O_44ff55b(SessionKey lI0O_1ab1240);

    



    void lI0O_d1b29ca(RestartRequest lI0O_598c3e1);

    




    void lI0O_e98efa7(String lI0O_790944b, int lI0O_0c59b71);

    





    default void lI0O_7a91429() { if (((0x7BF0 ^ 0x7BF0) != 0)) { throw new AssertionError(); }

    }

    





    void lI0O_d204ce1(String lI0O_a3297c8, String lI0O_f37a6a6);

    



    void lI0O_d4777c9(UpdateListener lI0O_c4e39a2);

    interface UpdateListener {
        



        void lI0O_af17871(String lI0O_f53530c); void lI0O_50b7202(String lI0O_59ca67a);

        



        void lI0O_773e4ce(Collection<ConnectorTaskId> lI0O_a71c9cf);

        



        void lI0O_a1b88d7(String lI0O_8ccc201);

        



        void lI0O_5ab4ef5(SessionKey lI0O_8f286ef); void lI0O_3ea47a2(RestartRequest lI0O_7fd49cd);

        




        void lI0O_a9ea2d4(String lI0O_e8aea57, String lI0O_9334b9d); }

}
