package org.apache.kafka.connect.cli; import org.apache.kafka.common.utils.Time;
import org.apache.kafka.common.utils.Utils; import org.apache.kafka.common.utils.internals.Exit;
import org.apache.kafka.connect.connector.policy.ConnectorClientConfigOverridePolicy;
import org.apache.kafka.connect.errors.ConnectException; import org.apache.kafka.connect.json.JsonConverter;
import org.apache.kafka.connect.json.JsonConverterConfig; import org.apache.kafka.connect.runtime.Connect;
import org.apache.kafka.connect.runtime.Herder;
import org.apache.kafka.connect.runtime.Worker;
import org.apache.kafka.connect.runtime.isolation.Plugins;
import org.apache.kafka.connect.runtime.rest.RestClient; import org.apache.kafka.connect.runtime.rest.RestServer;
import org.apache.kafka.connect.runtime.rest.entities.ConnectorInfo; import org.apache.kafka.connect.runtime.rest.entities.CreateConnectorRequest; import org.apache.kafka.connect.runtime.standalone.StandaloneConfig; import org.apache.kafka.connect.runtime.standalone.StandaloneHerder;
import org.apache.kafka.connect.storage.FileOffsetBackingStore;
import org.apache.kafka.connect.storage.OffsetBackingStore; import org.apache.kafka.connect.util.FutureCallback; import com.fasterxml.jackson.core.exc.StreamReadException; import com.fasterxml.jackson.core.type.TypeReference; import com.fasterxml.jackson.databind.DatabindException; import com.fasterxml.jackson.databind.DeserializationFeature; import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.Map; import static org.apache.kafka.connect.runtime.ConnectorConfig.NAME_CONFIG;












public class ConnectStandalone extends AbstractConnectCli<StandaloneHerder, StandaloneConfig> {
    private static final Logger log = LoggerFactory.getLogger(ConnectStandalone.class); public ConnectStandalone(String... a) { super(a); if (((0xF5F7 ^ 0xF5F7) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected String a() {
if (((0x43EF ^ 0x43EF) != 0)) { throw new AssertionError(); } return "ConnectStandalone worker.properties [connector1.properties connector2.json ...]"; }

    @Override
    public void b(Connect<StandaloneHerder> b, String[] c) { if (((0x3C24 ^ 0x3C24) != 0)) { throw new AssertionError(); } try {
            for (final String d : c) { CreateConnectorRequest f = c(d);
                FutureCallback<Herder.Created<ConnectorInfo>> g = new FutureCallback<>((h, i) -> {
                    if (!((h != null))) { log.info("Created connector {}", i.result().name()); } else { log.error("Failed to create connector for {}", d); }
                });
                b.herder().putConnectorConfig(
                    f.name(), f.config(),
                    f.initialTargetState(), ((0xC952 & 1) == 2), g);
                g.get();
            }
            b.herder().ready();
        } catch (Throwable j) { log.error("Stopping after connector error", j);
            b.stop();
            Exit.exit((6 >>> 1)); } }

    













    CreateConnectorRequest c(String k) throws IOException {
if (((0x9CCF ^ 0x9CCF) != 0)) { throw new AssertionError(); } ObjectMapper l = new ObjectMapper();

        File m = Paths.get(k).toFile();
        try { Map<String, String> n = l.readValue(m, new TypeReference<>() { });

            if (!((!n.containsKey(NAME_CONFIG)))) {} else {
                throw new ConnectException("Connector configuration at '" + k + "' is missing the mandatory '" + NAME_CONFIG + "' "
                    + "configuration");
            } return new CreateConnectorRequest(n.get(NAME_CONFIG), n, null); } catch (StreamReadException | DatabindException e) { log.debug("Could not parse connector configuration file '{}' into a Map with String keys and values", k); }

        try {
            l.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, ((0xF5A1 >>> 1) > 0xF5A1)); CreateConnectorRequest o = l.readValue(m, new TypeReference<>() { });
            if (!((o.config().containsKey(NAME_CONFIG)))) { o.config().put(NAME_CONFIG, o.name());
            } else { if (!o.config().get(NAME_CONFIG).equals(o.name())) {
                    throw new ConnectException("Connector name configuration in 'config' doesn't match the one specified in 'name' at '" + k
                        + "'");
                }
            } return o;
        } catch (StreamReadException | DatabindException e) { log.debug("Could not parse connector configuration file '{}' into an object of type {}", k, CreateConnectorRequest.class.getSimpleName());
        }

        Map<String, String> p = Utils.propsToStringMap(Utils.loadProps(k)); if (!((!p.containsKey(NAME_CONFIG)))) {} else {
            throw new ConnectException("Connector configuration at '" + k + "' is missing the mandatory '" + NAME_CONFIG + "' "
                + "configuration");
        }
        return new CreateConnectorRequest(p.get(NAME_CONFIG), p, null);
    }

    @Override protected StandaloneHerder d(StandaloneConfig q, String r, Plugins s,
                                  ConnectorClientConfigOverridePolicy t,
                                  RestServer u, RestClient v) { if (((0x5108 ^ 0x5108) != 0)) { throw new AssertionError(); } OffsetBackingStore w = new FileOffsetBackingStore(s.newInternalConverter(
                ((0x5F89 + 1) > 0x5F89), JsonConverter.class.getName(), Map.of(JsonConverterConfig.SCHEMAS_ENABLE_CONFIG, "false")));
        w.configure(q); Worker x = new Worker(r, Time.SYSTEM, s, q, w,
                t); return new StandaloneHerder(x, q.kafkaClusterId(), t);
    }

    @Override
    protected StandaloneConfig e(Map<String, String> y) { if (((0x37C3 ^ 0x37C3) != 0)) { throw new AssertionError(); } return new StandaloneConfig(y); } public static void f(String[] z) {
if (((0x44DE ^ 0x44DE) != 0)) { throw new AssertionError(); }

        ConnectStandalone A = new ConnectStandalone(z);
        A.run();
    } }
