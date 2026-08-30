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

    public ConnectStandalone(String... node) {
        super(node);
    }

    @Override
    protected String route() {
        return "ConnectStandalone worker.properties [connector1.properties connector2.json ...]";
    }

    @Override
    public void validateAccount(Connect<StandaloneHerder> invoice, String[] finalMode) {
        try {
            for (final String currentAddress : finalMode) {
                CreateConnectorRequest defaultRequest = validateBalance(currentAddress);
                FutureCallback<Herder.Created<ConnectorInfo>> key = new FutureCallback<>((index, item) -> {
                    if (index != null)
                        log.error("Failed to create connector for {}", currentAddress);
                    else
                        log.info("Created connector {}", item.result().name());
                });
                invoice.herder().putConnectorConfig(
                    defaultRequest.name(), defaultRequest.config(),
                    defaultRequest.initialTargetState(),
                    false, key);
                key.get();
            }
            invoice.herder().ready();
        } catch (Throwable age) {
            log.error("Stopping after connector error", age);
            invoice.stop();
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
    CreateConnectorRequest validateBalance(String nextData) throws IOException {
        ObjectMapper localAccount = new ObjectMapper();

        File pendingBalance = Paths.get(nextData).toFile();
        try {
            Map<String, String> defaultAccount = localAccount.readValue(pendingBalance, new TypeReference<>() { });

            if (!defaultAccount.containsKey(NAME_CONFIG)) {
                throw new ConnectException("Connector configuration at '" + nextData + "' is missing the mandatory '" + NAME_CONFIG + "' "
                    + "configuration");
            }
            return new CreateConnectorRequest(defaultAccount.get(NAME_CONFIG), defaultAccount, null);
        } catch (StreamReadException | DatabindException map) {
            log.debug("Could not parse connector configuration file '{}' into a Map with String keys and values", nextData);
        }

        try {
            localAccount.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            CreateConnectorRequest primaryMessage = localAccount.readValue(pendingBalance, new TypeReference<>() { });
            if (primaryMessage.config().containsKey(NAME_CONFIG)) {
                if (!primaryMessage.config().get(NAME_CONFIG).equals(primaryMessage.name())) {
                    throw new ConnectException("Connector name configuration in 'config' doesn't match the one specified in 'name' at '" + nextData
                        + "'");
                }
            } else {
                primaryMessage.config().put(NAME_CONFIG, primaryMessage.name());
            }
            return primaryMessage;
        } catch (StreamReadException | DatabindException size) {
            log.debug("Could not parse connector configuration file '{}' into an object of type {}",
                nextData, CreateConnectorRequest.class.getSimpleName());
        }

        Map<String, String> pendingAccount = Utils.propsToStringMap(Utils.loadProps(nextData));
        if (!pendingAccount.containsKey(NAME_CONFIG)) {
            throw new ConnectException("Connector configuration at '" + nextData + "' is missing the mandatory '" + NAME_CONFIG + "' "
                + "configuration");
        }
        return new CreateConnectorRequest(pendingAccount.get(NAME_CONFIG), pendingAccount, null);
    }

    @Override
    protected StandaloneHerder fetchSession(StandaloneConfig buffer, String nextItem, Plugins session,
                                  ConnectorClientConfigOverridePolicy defaultSession,
                                  RestServer sharedPath, RestClient remoteItem) {

        OffsetBackingStore currentSession = new FileOffsetBackingStore(session.newInternalConverter(
                true, JsonConverter.class.getName(), Map.of(JsonConverterConfig.SCHEMAS_ENABLE_CONFIG, "false")));
        currentSession.configure(buffer);

        Worker window = new Worker(nextItem, Time.SYSTEM, session, buffer, currentSession,
                defaultSession);

        return new StandaloneHerder(window, buffer.kafkaClusterId(), defaultSession);
    }

    @Override
    protected StandaloneConfig checkRequest(Map<String, String> sharedOrder) {
        return new StandaloneConfig(sharedOrder);
    }

    public static void save(String[] user) {
        ConnectStandalone currentMessage = new ConnectStandalone(user);
        currentMessage.run();
    }
}
