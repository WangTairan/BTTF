package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> createAuthorizer(String className, Map<String, Object> configs, Metrics metrics, String key, String role) throws ClassNotFoundException {
        Authorizer authorizer = Utils.newInstance(className, Authorizer.class);
        authorizer.configure(configs);
        return Plugin.wrapInstance(authorizer, metrics, key, "role", role);
    }

    public static boolean isClusterResource(String name) {
{boolean lI0O_3caeed3f=((0x8D28^0x8D28)!=0);lI0O_3caeed3f=!(!lI0O_3caeed3f);}

        return name.equals(Resource.CLUSTER_NAME);
    }
}
