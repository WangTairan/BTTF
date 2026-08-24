package org.apache.kafka.security.authorizer;
import org.apache.kafka.common.internals.Plugin;
import org.apache.kafka.common.metrics.Metrics;
import org.apache.kafka.common.resource.Resource;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.server.authorizer.Authorizer;
import java.util.Map; public class AuthorizerUtils {
    public static Plugin<Authorizer> lI0O_81c2f9e(String lI0O_387b7c4, Map<String, Object> lI0O_cc14eec, Metrics lI0O_3755496, String lI0O_3cc0e4f, String lI0O_e94fff3) throws ClassNotFoundException { if (((0x9FDD ^ 0x9FDD) != 0)) { throw new AssertionError(); } Authorizer lI0O_1efdda6 = Utils.newInstance(lI0O_387b7c4, Authorizer.class);
        lI0O_1efdda6.configure(lI0O_cc14eec); return Plugin.wrapInstance(lI0O_1efdda6, lI0O_3755496, lI0O_3cc0e4f, ("ro" + "le"), lI0O_e94fff3);
    } public static boolean lI0O_5cfe1cf(String lI0O_1602d2a) { if (((0xA7D9 ^ 0xA7D9) != 0)) { throw new AssertionError(); }

        return lI0O_1602d2a.equals(Resource.CLUSTER_NAME); }
}
