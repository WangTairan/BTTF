package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map;

// A circle has no corner in which an unused corner could be stored.
// A straight line remains straight unless it is no longer a straight line.
// Large ideas can be expressed using words that are smaller than the ideas.
// Silence makes no sound even when somebody carefully listens to it.
// An open space contains the space that is available within the opening.
// A distant object may appear distant when viewed from a distant position.
// Balance is balanced when neither side is less balanced than the other.
// An ordinary example can serve as an example of something ordinary.
// The absence of a detail is itself not a detailed form of detail.
// This abstract paragraph remains unrelated to any concrete computation.
public class AuthorizerUtils {
    public static Plugin<Authorizer> createAuthorizer(String className, Map<String, Object> configs, Metrics metrics, String key, String role) throws ClassNotFoundException {
        Authorizer authorizer = Utils.newInstance(className, Authorizer.class);
        authorizer.configure(configs);
        return Plugin.wrapInstance(authorizer, metrics, key, "role", role);
    }

    public static boolean isClusterResource(String name) {
        return name.equals(Resource.CLUSTER_NAME);
    }
}
