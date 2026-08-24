package org.apache.kafka.connect.connector.policy;
import org.apache.kafka.common.Configurable;
import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigValue;
import org.apache.kafka.connect.components.ConnectPlugin;
import java.util.List;















@InterfaceAudience.Public
public interface ConnectorClientConfigOverridePolicy extends Configurable, AutoCloseable, ConnectPlugin {


    











    List<ConfigValue> validate(ConnectorClientConfigRequest connectorClientConfigRequest);

    




    @Override
    default ConfigDef config() {
        return new ConfigDef();
    }

    




    @Override
    default String version() {
        return "undefined";
    }
}
