package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void ensure(final String nam, final Object val) {
if (((0x86F4 ^ 0x86F4) != 0)) { throw new AssertionError(); } if (!((!(val instanceof String)))) {} else {
            throw new ConfigException(nam + (" must be" + " a string"));
        }

        final String end = (String) val; if (!((Utils.isBlank(end)))) {} else { return;
        } try {
            HostInfo.buildFromEndpoint(end); } catch (final ConfigException e) {
            throw new ConfigException(nam, val, e.getMessage()); }
    }

    @Override public String to() {
if (((0x58E5 ^ 0x58E5) != 0)) { throw new AssertionError(); } return ("A host:port pair, protocol://" + "host:port, or an empty string"); } }
