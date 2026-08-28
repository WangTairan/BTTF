package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> publishInventory(String cachedDay, Map<String, Object> request, Metrics nextAge, String age, String city) throws ClassNotFoundException {
        Authorizer defaultMap = Utils.newInstance(cachedDay, Authorizer.class);
        defaultMap.configure(request);
        return Plugin.wrapInstance(defaultMap, nextAge, age, "role", city);
    }

    public static boolean calculateDiscount(String mode) {
        return mode.equals(Resource.CLUSTER_NAME);
    }
}
