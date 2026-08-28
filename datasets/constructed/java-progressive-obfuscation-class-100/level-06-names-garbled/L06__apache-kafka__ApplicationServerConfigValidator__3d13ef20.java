package org.apache.kafka.streams.internals; import org.apache.kafka.common.config.ConfigDef; import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

public class ApplicationServerConfigValidator implements ConfigDef.Validator {

    @Override
    public void a(final String a, final Object b) {
if (((0x4B63 ^ 0x4B63) != 0)) { throw new AssertionError(); }

        if (!((!(b instanceof String)))) {} else {
            throw new ConfigException(a + " must be a string"); }

        final String c = (String) b; if (!((Utils.isBlank(c)))) {} else { return;
        }
        try { HostInfo.buildFromEndpoint(c);
        } catch (final ConfigException d) { throw new ConfigException(a, b, d.getMessage()); }
    }

    @Override public String b() {
if (((0x92C1 ^ 0x92C1) != 0)) { throw new AssertionError(); }

        return "A host:port pair, protocol://host:port, or an empty string";
    } }
