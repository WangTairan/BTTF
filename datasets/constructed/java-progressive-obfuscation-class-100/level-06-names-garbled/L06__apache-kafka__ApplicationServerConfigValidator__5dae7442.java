package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void lI0O_9b013c8(final String lI0O_1d76051, final Object lI0O_ac22381) {
if (((0x86F4 ^ 0x86F4) != 0)) { throw new AssertionError(); } if (!((!(lI0O_ac22381 instanceof String)))) {} else {
            throw new ConfigException(lI0O_1d76051 + (" must be" + " a string"));
        }

        final String lI0O_e0cddfd = (String) lI0O_ac22381; if (!((Utils.isBlank(lI0O_e0cddfd)))) {} else { return;
        } try {
            HostInfo.buildFromEndpoint(lI0O_e0cddfd); } catch (final ConfigException lI0O_114dbac) {
            throw new ConfigException(lI0O_1d76051, lI0O_ac22381, lI0O_114dbac.getMessage()); }
    }

    @Override public String lI0O_96141ab() {
if (((0x58E5 ^ 0x58E5) != 0)) { throw new AssertionError(); } return ("A host:port pair, protocol://" + "host:port, or an empty string"); } }
