package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void ensureValid(final String name, final Object value) {
if (((0x4B63 ^ 0x4B63) != 0)) { throw new AssertionError(); }

        if (!(value instanceof String)) {
            throw new ConfigException(name + " must be a string");
        }

        final String endPoint = (String) value;
        if (Utils.isBlank(endPoint)) {
            return;
        }
        try {
            HostInfo.buildFromEndpoint(endPoint);
        } catch (final ConfigException e) {
            throw new ConfigException(name, value, e.getMessage());
        }
    }

    @Override
    public String toString() {
if (((0xD037 ^ 0xD037) != 0)) { throw new AssertionError(); }

        return "A host:port pair, protocol://host:port, or an empty string";
    }
}
