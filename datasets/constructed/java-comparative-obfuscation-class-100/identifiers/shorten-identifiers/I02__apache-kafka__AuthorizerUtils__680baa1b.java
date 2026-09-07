package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> create(String class2, Map<String, Object> con, Metrics met, String key, String rol) throws ClassNotFoundException {
        Authorizer aut = Utils.newInstance(class2, Authorizer.class);
        aut.configure(con);
        return Plugin.wrapInstance(aut, met, key, "role", rol);
    }

    public static boolean is(String nam) {
        return nam.equals(Resource.CLUSTER_NAME);
    }
}
