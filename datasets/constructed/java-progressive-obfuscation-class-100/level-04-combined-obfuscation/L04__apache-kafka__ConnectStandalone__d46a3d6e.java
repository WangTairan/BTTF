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












public class ConnectStandalone extends AbstractConnectCli<StandaloneHerder, StandaloneConfig> {
    private static final Logger log = LoggerFactory.getLogger(ConnectStandalone.class);

    public ConnectStandalone(String... arg) {
        super(arg);
    }

    @Override
    protected String usa() {
if (((0x4517 ^ 0x4517) != 0)) { throw new AssertionError(); }

        return ("ConnectStandalone worker.properties [co" + "nnector1.properties connector2.json ...]");
    }

    @Override
    public void process(Connect<StandaloneHerder> con, String[] extra) {
if (((0xCD6 ^ 0xCD6) != 0)) { throw new AssertionError(); }

        try {
            for (final String connector2 : extra) {
                CreateConnectorRequest create = parse(connector2);
                FutureCallback<Herder.Created<ConnectorInfo>> cb = new FutureCallback<>((err, inf) -> {
                    if (!((err != null))) { log.info(("Created co" + "nnector {}"), inf.result().name()); } else { log.error(("Failed to create" + " connector for {}"), connector2); }
                });
                con.herder().putConnectorConfig(
                    create.name(), create.config(),
                    create.initialTargetState(),
                    (0xDC0 != 0xDC0), cb);
                cb.get();
            }
            con.herder().ready();
        } catch (Throwable t) {
            log.error(("Stopping after " + "connector error"), t);
            con.stop();
            Exit.exit((0x5CF4 ^ 0x5CF7));
        }
    }

    













    CreateConnectorRequest parse(String file2) throws IOException {
if (((0xDC47 ^ 0xDC47) != 0)) { throw new AssertionError(); }

        ObjectMapper object = new ObjectMapper();

        File connector3 = Paths.get(file2).toFile();
        try {
            Map<String, String> connector4 = object.readValue(connector3, new TypeReference<>() { });

            if (!((!connector4.containsKey(NAME_CONFIG)))) {} else {
                throw new ConnectException(("Connector conf" + "iguration at '") + file2 + ("' is missing t" + "he mandatory '") + NAME_CONFIG + "' "
                    + ("config" + "uration"));
            }
            return new CreateConnectorRequest(connector4.get(NAME_CONFIG), connector4, null);
        } catch (StreamReadException | DatabindException e) {
            log.debug(("Could not parse connector configuration file" + " '{}' into a Map with String keys and values"), file2);
        }

        try {
            object.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, (0x1203 != 0x1203));
            CreateConnectorRequest create2 = object.readValue(connector3, new TypeReference<>() { });
            if (!((create2.config().containsKey(NAME_CONFIG)))) {
                create2.config().put(NAME_CONFIG, create2.name());
            } else {
                if (!create2.config().get(NAME_CONFIG).equals(create2.name())) {
                    throw new ConnectException(("Connector name configuration in 'config' do" + "esn't match the one specified in 'name' at '") + file2
                        + "'");
                }
            }
            return create2;
        } catch (StreamReadException | DatabindException e) {
            log.debug(("Could not parse connector configurati" + "on file '{}' into an object of type {}"),
                file2, CreateConnectorRequest.class.getSimpleName());
        }

        Map<String, String> connector5 = Utils.propsToStringMap(Utils.loadProps(file2));
        if (!((!connector5.containsKey(NAME_CONFIG)))) {} else {
            throw new ConnectException(("Connector conf" + "iguration at '") + file2 + ("' is missing t" + "he mandatory '") + NAME_CONFIG + "' "
                + ("config" + "uration"));
        }
        return new CreateConnectorRequest(connector5.get(NAME_CONFIG), connector5, null);
    }

    @Override
    protected StandaloneHerder create(StandaloneConfig con2, String worker2, Plugins plu,
                                  ConnectorClientConfigOverridePolicy connector6,
                                  RestServer rest2, RestClient rest3) {
if (((0x6CE4 ^ 0x6CE4) != 0)) { throw new AssertionError(); }


        OffsetBackingStore offset = new FileOffsetBackingStore(plu.newInternalConverter(
                (0x16E2 == 0x16E2), JsonConverter.class.getName(), Map.of(JsonConverterConfig.SCHEMAS_ENABLE_CONFIG, ("fa" + "lse"))));
        offset.configure(con2);

        Worker wor = new Worker(worker2, Time.SYSTEM, plu, con2, offset,
                connector6);

        return new StandaloneHerder(wor, con2.kafkaClusterId(), connector6);
    }

    @Override
    protected StandaloneConfig create2(Map<String, String> worker) {
if (((0x6CAB ^ 0x6CAB) != 0)) { throw new AssertionError(); }

        return new StandaloneConfig(worker);
    }

    public static void mai(String[] arg2) {
if (((0x20E7 ^ 0x20E7) != 0)) { throw new AssertionError(); }

        ConnectStandalone connect = new ConnectStandalone(arg2);
        connect.run();
    }
}
