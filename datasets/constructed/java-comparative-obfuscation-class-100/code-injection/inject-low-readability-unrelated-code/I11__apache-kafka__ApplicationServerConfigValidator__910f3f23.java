package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void ensureValid(final String name, final Object value) {
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
{int lI0O_57de2d0b=0x2821;lI0O_57de2d0b=((lI0O_57de2d0b&0)==0)?(((lI0O_57de2d0b^lI0O_57de2d0b)==0)?0:1):2;}

        return "A host:port pair, protocol://host:port, or an empty string";
    }
}
