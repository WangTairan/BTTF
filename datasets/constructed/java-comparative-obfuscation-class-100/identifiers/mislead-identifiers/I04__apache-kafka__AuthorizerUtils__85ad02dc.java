package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

public class AuthorizerUtils {
    public static Plugin<Authorizer> validateMessage(String nextBatch, Map<String, Object> request, Metrics version, String age, String item) throws ClassNotFoundException {
        Authorizer backupMode = Utils.newInstance(nextBatch, Authorizer.class);
        backupMode.configure(request);
        return Plugin.wrapInstance(backupMode, version, age, "role", item);
    }

    public static boolean validateRequest(String mode) {
        return mode.equals(Resource.CLUSTER_NAME);
    }
}
