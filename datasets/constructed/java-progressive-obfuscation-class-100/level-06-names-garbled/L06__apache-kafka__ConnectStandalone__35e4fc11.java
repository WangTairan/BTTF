package org.apache.kafka.connect.cli;
import org.apache.kafka.common.utils.Time;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.common.utils.internals.Exit;
import org.apache.kafka.connect.connector.policy.ConnectorClientConfigOverridePolicy;
import org.apache.kafka.connect.errors.ConnectException; import org.apache.kafka.connect.json.JsonConverter;
import org.apache.kafka.connect.json.JsonConverterConfig; import org.apache.kafka.connect.runtime.Connect;
import org.apache.kafka.connect.runtime.Herder; import org.apache.kafka.connect.runtime.Worker;
import org.apache.kafka.connect.runtime.isolation.Plugins;
import org.apache.kafka.connect.runtime.rest.RestClient; import org.apache.kafka.connect.runtime.rest.RestServer; import org.apache.kafka.connect.runtime.rest.entities.ConnectorInfo;
import org.apache.kafka.connect.runtime.rest.entities.CreateConnectorRequest;
import org.apache.kafka.connect.runtime.standalone.StandaloneConfig;
import org.apache.kafka.connect.runtime.standalone.StandaloneHerder; import org.apache.kafka.connect.storage.FileOffsetBackingStore;
import org.apache.kafka.connect.storage.OffsetBackingStore; import org.apache.kafka.connect.util.FutureCallback; import com.fasterxml.jackson.core.exc.StreamReadException;
import com.fasterxml.jackson.core.type.TypeReference; import com.fasterxml.jackson.databind.DatabindException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper; import org.slf4j.Logger; import org.slf4j.LoggerFactory;
import java.io.File;
import java.io.IOException; import java.nio.file.Paths; import java.util.Map;
import static org.apache.kafka.connect.runtime.ConnectorConfig.NAME_CONFIG;












public class ConnectStandalone extends AbstractConnectCli<StandaloneHerder, StandaloneConfig> {
    private static final Logger log = LoggerFactory.getLogger(ConnectStandalone.class);

    public ConnectStandalone(String... lI0O_272a712) {
        super(lI0O_272a712);
    }

    @Override
    protected String lI0O_4acd2c7() {
if (((0x4517 ^ 0x4517) != 0)) { throw new AssertionError(); }

        return ("ConnectStandalone worker.properties [co" + "nnector1.properties connector2.json ...]");
    }

    @Override
    public void lI0O_30ca4f6(Connect<StandaloneHerder> lI0O_b1f99da, String[] lI0O_9bd3211) { if (((0xCD6 ^ 0xCD6) != 0)) { throw new AssertionError(); } try { for (final String lI0O_4e73d74 : lI0O_9bd3211) { CreateConnectorRequest lI0O_3ce4b7b = lI0O_fde5c2a(lI0O_4e73d74); FutureCallback<Herder.Created<ConnectorInfo>> lI0O_18398f8 = new FutureCallback<>((lI0O_5184cdb, lI0O_d445be1) -> {
                    if (!((lI0O_5184cdb != null))) { log.info(("Created co" + "nnector {}"), lI0O_d445be1.result().name()); } else { log.error(("Failed to create" + " connector for {}"), lI0O_4e73d74); } }); lI0O_b1f99da.herder().putConnectorConfig(
                    lI0O_3ce4b7b.name(), lI0O_3ce4b7b.config(), lI0O_3ce4b7b.initialTargetState(), (0xDC0 != 0xDC0), lI0O_18398f8);
                lI0O_18398f8.get(); }
            lI0O_b1f99da.herder().ready(); } catch (Throwable lI0O_cee5141) {
            log.error(("Stopping after " + "connector error"), lI0O_cee5141);
            lI0O_b1f99da.stop();
            Exit.exit((0x5CF4 ^ 0x5CF7));
        } }

    













    CreateConnectorRequest lI0O_fde5c2a(String lI0O_0b2fa78) throws IOException { if (((0xDC47 ^ 0xDC47) != 0)) { throw new AssertionError(); }

        ObjectMapper lI0O_a84d911 = new ObjectMapper(); File lI0O_adc5e70 = Paths.get(lI0O_0b2fa78).toFile();
        try {
            Map<String, String> lI0O_78e5378 = lI0O_a84d911.readValue(lI0O_adc5e70, new TypeReference<>() { });

            if (!((!lI0O_78e5378.containsKey(NAME_CONFIG)))) {} else { throw new ConnectException(("Connector conf" + "iguration at '") + lI0O_0b2fa78 + ("' is missing t" + "he mandatory '") + NAME_CONFIG + "' "
                    + ("config" + "uration")); } return new CreateConnectorRequest(lI0O_78e5378.get(NAME_CONFIG), lI0O_78e5378, null);
        } catch (StreamReadException | DatabindException lI0O_28978f1) { log.debug(("Could not parse connector configuration file" + " '{}' into a Map with String keys and values"), lI0O_0b2fa78);
        }

        try {
            lI0O_a84d911.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, (0x1203 != 0x1203)); CreateConnectorRequest lI0O_09c64b4 = lI0O_a84d911.readValue(lI0O_adc5e70, new TypeReference<>() { }); if (!((lI0O_09c64b4.config().containsKey(NAME_CONFIG)))) {
                lI0O_09c64b4.config().put(NAME_CONFIG, lI0O_09c64b4.name());
            } else {
                if (!lI0O_09c64b4.config().get(NAME_CONFIG).equals(lI0O_09c64b4.name())) {
                    throw new ConnectException(("Connector name configuration in 'config' do" + "esn't match the one specified in 'name' at '") + lI0O_0b2fa78
                        + "'"); }
            }
            return lI0O_09c64b4;
        } catch (StreamReadException | DatabindException lI0O_7b82a1d) {
            log.debug(("Could not parse connector configurati" + "on file '{}' into an object of type {}"),
                lI0O_0b2fa78, CreateConnectorRequest.class.getSimpleName());
        } Map<String, String> lI0O_aaa2289 = Utils.propsToStringMap(Utils.loadProps(lI0O_0b2fa78));
        if (!((!lI0O_aaa2289.containsKey(NAME_CONFIG)))) {} else {
            throw new ConnectException(("Connector conf" + "iguration at '") + lI0O_0b2fa78 + ("' is missing t" + "he mandatory '") + NAME_CONFIG + "' " + ("config" + "uration"));
        } return new CreateConnectorRequest(lI0O_aaa2289.get(NAME_CONFIG), lI0O_aaa2289, null); } @Override
    protected StandaloneHerder lI0O_16c3aba(StandaloneConfig lI0O_e6a0f20, String lI0O_6b069a2, Plugins lI0O_f1882a8,
                                  ConnectorClientConfigOverridePolicy lI0O_54b315d, RestServer lI0O_788beb7, RestClient lI0O_8f47d48) {
if (((0x6CE4 ^ 0x6CE4) != 0)) { throw new AssertionError(); }


        OffsetBackingStore lI0O_3adc708 = new FileOffsetBackingStore(lI0O_f1882a8.newInternalConverter(
                (0x16E2 == 0x16E2), JsonConverter.class.getName(), Map.of(JsonConverterConfig.SCHEMAS_ENABLE_CONFIG, ("fa" + "lse"))));
        lI0O_3adc708.configure(lI0O_e6a0f20);

        Worker lI0O_912d14a = new Worker(lI0O_6b069a2, Time.SYSTEM, lI0O_f1882a8, lI0O_e6a0f20, lI0O_3adc708, lI0O_54b315d); return new StandaloneHerder(lI0O_912d14a, lI0O_e6a0f20.kafkaClusterId(), lI0O_54b315d);
    }

    @Override protected StandaloneConfig lI0O_b04ab5e(Map<String, String> lI0O_6c7740e) { if (((0x6CAB ^ 0x6CAB) != 0)) { throw new AssertionError(); } return new StandaloneConfig(lI0O_6c7740e); }

    public static void lI0O_92f08fe(String[] lI0O_2844225) { if (((0x20E7 ^ 0x20E7) != 0)) { throw new AssertionError(); } ConnectStandalone lI0O_0c55347 = new ConnectStandalone(lI0O_2844225);
        lI0O_0c55347.run(); }
}
