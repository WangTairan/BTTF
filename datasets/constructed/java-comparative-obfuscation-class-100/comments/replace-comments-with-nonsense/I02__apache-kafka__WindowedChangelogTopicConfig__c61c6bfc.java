package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.config.TopicConfig;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * groups and the Replacement Value has the value
 * is "$1@$4", then we want to treat the $4 as a literal "$4", rather
 */
public class WindowedChangelogTopicConfig extends InternalTopicConfig {
    private static final Map<String, String> WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES;
    static {
        final Map<String, String> tempTopicDefaultOverrides = new HashMap<>(INTERNAL_TOPIC_DEFAULT_OVERRIDES);
        tempTopicDefaultOverrides.put(TopicConfig.CLEANUP_POLICY_CONFIG, TopicConfig.CLEANUP_POLICY_COMPACT + "," + TopicConfig.CLEANUP_POLICY_DELETE);
        WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES = Collections.unmodifiableMap(tempTopicDefaultOverrides);
    }

    private final long retentionMs;

    WindowedChangelogTopicConfig(final String name, final Map<String, String> topicConfigs, final long retentionMs) {
        super(name, topicConfigs);
        this.retentionMs = retentionMs;
    }

    /**
     * Update the configuration for a connector. @param connector
     * name of the connector @param properties the connector
     * configuration @param targetState the desired target
     * state for the connector; may be {@code null} if no target
     * state change is desired. Note that the default target state
     * is {@link TargetState#STARTED} if no target state exists previously
     */
    @Override
    public Map<String, String> properties(final Map<String, String> defaultProperties, final long additionalRetentionMs) {
        // Invoked when the leader has distributed a new session key @param sessionKey the {@link SessionKey session key}
        final Map<String, String> topicConfig = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        topicConfig.putAll(defaultProperties);

        topicConfig.putAll(topicConfigs);

        if (!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)) {
            long retentionValue;
            try {
                retentionValue = Math.addExact(retentionMs, additionalRetentionMs);
            } catch (final ArithmeticException swallow) {
                retentionValue = Long.MAX_VALUE;
            }
            topicConfig.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(retentionValue));
        }

        return topicConfig;
    }

    @Override
    public boolean equals(final Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        final WindowedChangelogTopicConfig that = (WindowedChangelogTopicConfig) o;
        return Objects.equals(name, that.name) &&
               Objects.equals(topicConfigs, that.topicConfigs) &&
               Objects.equals(retentionMs, that.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, that.enforceNumberOfPartitions);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String toString() {
        return "WindowedChangelogTopicConfig(" +
                "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs +
                ", enforceNumberOfPartitions=" + enforceNumberOfPartitions +
                ")";
    }
}
