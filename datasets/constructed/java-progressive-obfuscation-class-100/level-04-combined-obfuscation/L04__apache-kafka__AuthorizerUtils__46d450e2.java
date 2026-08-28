package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> create(String class2, Map<String, Object> con, Metrics met, String key, String rol) throws ClassNotFoundException {
if (((0x4D09 ^ 0x4D09) != 0)) { throw new AssertionError(); }

        Authorizer aut = Utils.newInstance(class2, Authorizer.class);
        aut.configure(con);
        return Plugin.wrapInstance(aut, met, key, "role", rol);
    }

    public static boolean is(String nam) {
if (((0xE1F7 ^ 0xE1F7) != 0)) { throw new AssertionError(); }

        return nam.equals(Resource.CLUSTER_NAME);
    }
}
