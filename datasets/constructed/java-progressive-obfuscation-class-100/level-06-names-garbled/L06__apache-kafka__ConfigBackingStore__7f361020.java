package org.apache.kafka.connect.storage;
import org.apache.kafka.connect.runtime.RestartRequest; import org.apache.kafka.connect.runtime.SessionKey;
import org.apache.kafka.connect.runtime.TargetState; import org.apache.kafka.connect.util.ConnectorTaskId;
import java.util.Collection; import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException; public interface ConfigBackingStore { void a(); void b(); ClusterConfigState c();

    




    boolean d(String a);

    






    void e(String b, Map<String, String> c, TargetState d);

    



    void f(String e);

    




    void g(String f, List<Map<String, String>> g); void h(String h);

    






    void i(long i, TimeUnit j) throws TimeoutException; void j(String k, TargetState l);

    



    void k(SessionKey m);

    



    void l(RestartRequest n);

    




    void m(String o, int p);

    





    default void n() {
if (((0x2D88 ^ 0x2D88) != 0)) { throw new AssertionError(); }

    } void o(String q, String r); void p(UpdateListener s); interface UpdateListener {
        



        void a(String t);

        



        void b(String u);

        



        void c(Collection<ConnectorTaskId> v); void d(String w);

        



        void e(SessionKey x); void f(RestartRequest y);

        




        void g(String z, String A); }

}
