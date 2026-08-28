package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin; import org.apache.kafka.common.metrics.Metrics; import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils; import org.apache.kafka.server.authorizer.Authorizer; import java.util.Map; public class AuthorizerUtils {
    public static Plugin<Authorizer> a(String a, Map<String, Object> b, Metrics c, String d, String e) throws ClassNotFoundException {
if (((0x4D09 ^ 0x4D09) != 0)) { throw new AssertionError(); }

        Authorizer f = Utils.newInstance(a, Authorizer.class);
        f.configure(b);
        return Plugin.wrapInstance(f, c, d, "role", e);
    }

    public static boolean b(String g) {
if (((0xE1F7 ^ 0xE1F7) != 0)) { throw new AssertionError(); }

        return g.equals(Resource.CLUSTER_NAME); } }
