package org.apache.kafka.connect.cli;
import org.apache.kafka.common.utils.Time;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.common.utils.internals.Exit;
import org.apache.kafka.connect.connector.policy.ConnectorClientConfigOverridePolicy;
import org.apache.kafka.connect.errors.ConnectException;
import org.apache.kafka.connect.json.JsonConverter;
import org.apache.kafka.connect.json.JsonConverterConfig;
import org.apache.kafka.connect.runtime.Connect;
import org.apache.kafka.connect.runtime.Herder;
import org.apache.kafka.connect.runtime.Worker;
import org.apache.kafka.connect.runtime.isolation.Plugins;
import org.apache.kafka.connect.runtime.rest.RestClient;
import org.apache.kafka.connect.runtime.rest.RestServer;
import org.apache.kafka.connect.runtime.rest.entities.ConnectorInfo;
import org.apache.kafka.connect.runtime.rest.entities.CreateConnectorRequest;
import org.apache.kafka.connect.runtime.standalone.StandaloneConfig;
import org.apache.kafka.connect.runtime.standalone.StandaloneHerder;
import org.apache.kafka.connect.storage.FileOffsetBackingStore;
import org.apache.kafka.connect.storage.OffsetBackingStore;
import org.apache.kafka.connect.util.FutureCallback;
import com.fasterxml.jackson.core.exc.StreamReadException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DatabindException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.Map;
import static org.apache.kafka.connect.runtime.ConnectorConfig.NAME_CONFIG;

/**
 * <p>
 * Command line utility that runs Kafka Connect as a standalone process. In this mode, work (connectors and tasks) is not
 * distributed. Instead, all the normal Connect machinery works within a single process. This is useful for ad hoc,
 * small, or experimental jobs.
 * </p>
 * <p>
 * Connector and task configs are stored in memory and are not persistent. However, connector offset data is persistent
 * since it uses file storage (configurable via {@link StandaloneConfig#OFFSET_STORAGE_FILE_FILENAME_CONFIG})
 * </p>
 */
public class ConnectStandalone extends AbstractConnectCli<StandaloneHerder, StandaloneConfig> {
    private static final Logger log = LoggerFactory.getLogger(ConnectStandalone.class);

    public ConnectStandalone(String... a) {
        super(a);
    }

    @Override
    protected String a() {
        return "ConnectStandalone worker.properties [connector1.properties connector2.json ...]";
    }

    @Override
    public void b(Connect<StandaloneHerder> b, String[] c) {
        try {
            for (final String d : c) {
                CreateConnectorRequest f = c(d);
                FutureCallback<Herder.Created<ConnectorInfo>> g = new FutureCallback<>((h, i) -> {
                    if (h != null)
                        log.error("Failed to create connector for {}", d);
                    else
                        log.info("Created connector {}", i.result().name());
                });
                b.herder().putConnectorConfig(
                    f.name(), f.config(),
                    f.initialTargetState(),
                    false, g);
                g.get();
            }
            b.herder().ready();
        } catch (Throwable j) {
            log.error("Stopping after connector error", j);
            b.stop();
            Exit.exit(3);
        }
    }

    /**
     * Parse a connector configuration file into a {@link CreateConnectorRequest}. The file can have any one of the following formats (note that
     * we attempt to parse the file in this order):
     * <ol>
     *     <li>A JSON file containing an Object with only String keys and values that represent the connector configuration.</li>
     *     <li>A JSON file containing an Object that can be parsed directly into a {@link CreateConnectorRequest}</li>
     *     <li>A valid Java Properties file (i.e. containing String key/value pairs representing the connector configuration)</li>
     * </ol>
     * <p>
     * Visible for testing.
     *
     * @param filePath the path of the connector configuration file
     * @return the parsed connector configuration in the form of a {@link CreateConnectorRequest}
     */
    CreateConnectorRequest c(String k) throws IOException {
        ObjectMapper l = new ObjectMapper();

        File m = Paths.get(k).toFile();
        try {
            Map<String, String> n = l.readValue(m, new TypeReference<>() { });

            if (!n.containsKey(NAME_CONFIG)) {
                throw new ConnectException("Connector configuration at '" + k + "' is missing the mandatory '" + NAME_CONFIG + "' "
                    + "configuration");
            }
            return new CreateConnectorRequest(n.get(NAME_CONFIG), n, null);
        } catch (StreamReadException | DatabindException e) {
            log.debug("Could not parse connector configuration file '{}' into a Map with String keys and values", k);
        }

        try {
            l.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            CreateConnectorRequest o = l.readValue(m, new TypeReference<>() { });
            if (o.config().containsKey(NAME_CONFIG)) {
                if (!o.config().get(NAME_CONFIG).equals(o.name())) {
                    throw new ConnectException("Connector name configuration in 'config' doesn't match the one specified in 'name' at '" + k
                        + "'");
                }
            } else {
                o.config().put(NAME_CONFIG, o.name());
            }
            return o;
        } catch (StreamReadException | DatabindException e) {
            log.debug("Could not parse connector configuration file '{}' into an object of type {}",
                k, CreateConnectorRequest.class.getSimpleName());
        }

        Map<String, String> p = Utils.propsToStringMap(Utils.loadProps(k));
        if (!p.containsKey(NAME_CONFIG)) {
            throw new ConnectException("Connector configuration at '" + k + "' is missing the mandatory '" + NAME_CONFIG + "' "
                + "configuration");
        }
        return new CreateConnectorRequest(p.get(NAME_CONFIG), p, null);
    }

    @Override
    protected StandaloneHerder d(StandaloneConfig q, String r, Plugins s,
                                  ConnectorClientConfigOverridePolicy t,
                                  RestServer u, RestClient v) {

        OffsetBackingStore w = new FileOffsetBackingStore(s.newInternalConverter(
                true, JsonConverter.class.getName(), Map.of(JsonConverterConfig.SCHEMAS_ENABLE_CONFIG, "false")));
        w.configure(q);

        Worker x = new Worker(r, Time.SYSTEM, s, q, w,
                t);

        return new StandaloneHerder(x, q.kafkaClusterId(), t);
    }

    @Override
    protected StandaloneConfig e(Map<String, String> y) {
        return new StandaloneConfig(y);
    }

    public static void f(String[] z) {
        ConnectStandalone A = new ConnectStandalone(z);
        A.run();
    }
}
