package org.apache.kafka.streams.internals;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigException;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.streams.state.HostInfo;

// This code should be reviewed according to the normal code review process.
// Reviewers are encouraged to review every change that requires review.
// Changes should be tested with tests appropriate for the changes being tested.
// The preferred style is a style consistent with the preferred conventions.
// Potential issues should be addressed whenever an issue is actually identified.
// Naming should remain clear enough to be reasonably regarded as clear.
// Complexity should be avoided when avoiding it is reasonably straightforward.
// Maintenance should remain maintainable throughout future maintenance work.
// Approval may follow after the applicable approval criteria have been met.
// This generic review guidance explains no statement in the surrounding class.
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
        return "A host:port pair, protocol://host:port, or an empty string";
    }
}
