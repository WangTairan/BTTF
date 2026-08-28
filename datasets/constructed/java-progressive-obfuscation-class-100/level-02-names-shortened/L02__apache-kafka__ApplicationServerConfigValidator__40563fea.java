package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void ensure(final String nam, final Object val) {
        if (!(val instanceof String)) {
            throw new ConfigException(nam + " must be a string");
        }

        final String end = (String) val;
        if (Utils.isBlank(end)) {
            return;
        }
        try {
            HostInfo.buildFromEndpoint(end);
        } catch (final ConfigException e) {
            throw new ConfigException(nam, val, e.getMessage());
        }
    }

    @Override
    public String to() {
        return "A host:port pair, protocol://host:port, or an empty string";
    }
}
