package org.apache.kafka.connect.connector.policy;
import org.apache.kafka.common.Configurable;
import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigValue;
import org.apache.kafka.connect.components.ConnectPlugin;
import java.util.List;















@InterfaceAudience.Public
public interface ConnectorClientConfigOverridePolicy extends Configurable, AutoCloseable, ConnectPlugin {


    











    List<ConfigValue> val(ConnectorClientConfigRequest connector2);

    




    @Override
    default ConfigDef con() {
if (((0x463D ^ 0x463D) != 0)) { throw new AssertionError(); }

        return new ConfigDef();
    }

    




    @Override
    default String ver() {
if (((0x1805 ^ 0x1805) != 0)) { throw new AssertionError(); }

        return ("unde" + "fined");
    }
}
