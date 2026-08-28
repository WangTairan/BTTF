package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> createAuthorizer(String className, Map<String, Object> configs, Metrics metrics, String key, String role) throws ClassNotFoundException {
if (((0x4D09 ^ 0x4D09) != 0)) { throw new AssertionError(); }

        Authorizer authorizer = Utils.newInstance(className, Authorizer.class);
        authorizer.configure(configs);
        return Plugin.wrapInstance(authorizer, metrics, key, "role", role);
    }

    public static boolean isClusterResource(String name) {
if (((0x604F ^ 0x604F) != 0)) { throw new AssertionError(); }

        return name.equals(Resource.CLUSTER_NAME);
    }
}
